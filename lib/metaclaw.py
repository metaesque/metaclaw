import os
import shutil
import time
import json
import re
import subprocess
import sys
import textwrap
import markdown as md_lib

# ==============================================================================
# META<CLAW> CORE LIBRARY
# ==============================================================================

class Error(Exception):
  pass

class MetaClaw:
  def __init__(self):
    self._structure = None
    self._timestamp = 0

  def subpath(self, service=None, provider=None, subdir=None, base=None):
    """Returns a path within the Meta<Claw> directory hierarchy.

    Args:
      service : str
        If present, the uid (singular) of desired service (establishes the
        directory <root>/services/<service>)
      provider : str
        If present, the uid of desired provider (establishes the directory
        <root>/services/<service>/<provider>)
      subdir : str
        If present, establishes the directory <root>/<subdir>. Common values
        are 'workspace', 'lib', or 'bin'.
      base : str
        A base file within final directory (if null, directory path returned)
    """
    structure = self.structure()
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(lib_dir)
    result = root_dir

    if service:
      sdata = structure['services'].get(service, None)
      if not sdata:
        raise Error('Invalid service uid "%s"' % service)

      result = os.path.join(result, 'services', sdata['uids'])

      if provider:
        result = os.path.join(result, provider)

    if base:
      result = os.path.join(result, base)

    return result

  def structure(self):
    """
    Loads and returns the comprehensive MetaClaw service taxonomy by
    reconstructing it from modular JSON fragments.
    Uses internal caching
    based on file modification timestamps to prevent disk I/O bottlenecks.
    """
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(lib_dir)

    relevant_files = []

    tiers_path = os.path.join(root_dir, '.tiers.json')
    if os.path.exists(tiers_path):
      relevant_files.append(tiers_path)

    planes_path = os.path.join(root_dir, '.planes.json')
    if os.path.exists(planes_path):
      relevant_files.append(planes_path)

    services_dir = os.path.join(root_dir, 'services')
    if os.path.exists(services_dir):
      for svc_folder in os.listdir(services_dir):
        svc_folder_path = os.path.join(services_dir, svc_folder)
        if not os.path.isdir(svc_folder_path):
          continue

        svc_json = os.path.join(svc_folder_path, '.service.json')
        if os.path.exists(svc_json):
          relevant_files.append(svc_json)

        for prov_folder in os.listdir(svc_folder_path):
          prov_folder_path = os.path.join(svc_folder_path, prov_folder)
          if not os.path.isdir(prov_folder_path):
            continue

          prov_json = os.path.join(
            prov_folder_path, '.provider.json'
          )
          if os.path.exists(prov_json):
            relevant_files.append(prov_json)

    max_mtime = 0
    for fpath in relevant_files:
      mtime = os.path.getmtime(fpath)
      if mtime > max_mtime:
        max_mtime = mtime

    if self._structure is not None and max_mtime <= self._timestamp:
      return self._structure

    struct = {}

    if os.path.exists(tiers_path):
      with open(tiers_path, 'r', encoding='utf-8') as f:
        struct['tiers'] = json.load(f)

    if os.path.exists(planes_path):
      with open(planes_path, 'r', encoding='utf-8') as f:
        struct['planes'] = json.load(f)

    struct['services'] = {}

    if os.path.exists(services_dir):
      for svc_folder in os.listdir(services_dir):
        svc_folder_path = os.path.join(services_dir, svc_folder)
        if not os.path.isdir(svc_folder_path):
          continue

        svc_json_path = os.path.join(svc_folder_path, '.service.json')
        if os.path.exists(svc_json_path):
          with open(svc_json_path, 'r', encoding='utf-8') as f:
            svc_data = json.load(f)

          svc_key = svc_data.get('uid', svc_folder)
          svc_data['providers'] = {}

          # Load providers
          for prov_folder in os.listdir(svc_folder_path):
            prov_folder_path = os.path.join(svc_folder_path, prov_folder)
            if not os.path.isdir(prov_folder_path):
              continue

            prov_json_path = os.path.join(
              prov_folder_path, '.provider.json'
            )
            if os.path.exists(prov_json_path):
              with open(prov_json_path, 'r', encoding='utf-8') as pf:
                prov_data = json.load(pf)
                prov_key = prov_data.get('uid', prov_folder)
                svc_data['providers'][prov_key] = prov_data

          struct['services'][svc_key] = svc_data

    self._structure = struct
    self._timestamp = max_mtime
    return struct

  def updateCluster(
    self,
    profile,
    current_hostname,
    tier,
    planes,
    hardware,
    require_wan,
    is_headless,
    order_prefs
  ):
    """
    Analyzes the entire cluster and redistributes service providers based
    on the newly added node and the specific structural planes it represents.
    Handles 'teardown' logic by evicting overlapping planes from older nodes.
    Utilizes the order_prefs prioritization matrix to select the optimal providers.

    Args:
      profile (dict): The current cluster profile loaded from profile.json.
      current_hostname (str): The hostname of the node being profiled.
      tier (int): The target architectural tier (0-4) for this node.
      planes (list): A list of planes this node represents (e.g., ["control", "compute"]).
      hardware (dict): The hardware details dictionary for this node.
      require_wan (bool): Whether the node requires remote WAN access.
      is_headless (bool): Whether the node is a bare-metal headless server.
      order_prefs (list of str): Priority order for provider selection.

    Returns:
      dict: The updated cluster profile.
    """
    node = next((n for n in profile["nodes"] if n["hostname"] == current_hostname), None)
    if not node:
        node = {"hostname": current_hostname, "hardware": hardware}
        profile["nodes"].append(node)

    node["tier"] = tier
    node["planes"] = planes
    node["order_prefs"] = order_prefs
    node["require_wan"] = require_wan
    node["hardware"]["headless"] = is_headless
    node["hardware"].update(hardware)

    # ============================================================================
    # PLANE EVICTION LOGIC (CLUSTER RECONCILIATION)
    # ============================================================================
    # Ensure there is only one authoritative node per plane in the cluster.
    for other_node in profile["nodes"]:
        if other_node["hostname"] != current_hostname:
            other_node["planes"] = [p for p in other_node.get("planes", []) if p not in planes]

    # ============================================================================
    # PROVIDER RESOLUTION VIA MATRIX
    # ============================================================================
    struct = self.structure()
    all_planes = struct.get('planes', {})

    for n in profile["nodes"]:
        n_tier = n.get("tier", 0)
        n_os = n.get("hardware", {}).get("os", "Linux")
        n_order = ",".join(n.get("order_prefs", order_prefs))
        n_planes = n.get("planes", [])
        n_wan = n.get("require_wan", False)

        assigned_services = set()
        for p in n_planes:
            if p in all_planes:
                assigned_services.update(all_planes[p].get("services", []))

        if n_wan:
            assigned_services.add("network")

        new_providers = {}
        for svc_key in assigned_services:
            svc_data = struct.get('services', {}).get(svc_key, {})
            prov_uid = None
            metal = False

            # Check matrix for overriding providers
            if 'matrix' in svc_data:
                tier_key = f"tier-{n_tier}"
                matrix = svc_data['matrix']
                if tier_key in matrix and n_os in matrix[tier_key] and n_order in matrix[tier_key][n_os]:
                    decision = matrix[tier_key][n_os][n_order]
                    prov_uid = decision.get("uid")
                    metal = decision.get("metal", False)

            # Fallbacks if matrix misses or isn't defined
            if not prov_uid:
                fallbacks = {
                    "gateway": "openclaw",
                    "proxy": "litellm",
                    "logger": "victorialogs",
                    "cache": "redis",
                    "memory": "postgres",
                    "runner": "ollama",
                    "sandbox": "docker-dood" if n_os == "Darwin" else "gvisor",
                    "browser": "browseruse",
                    "fetcher": "crawl4ai",
                    "searcher": "searxng",
                    "ci": "woodpecker",
                    "vcs": "gitea",
                    "network": "tailscale",
                    "proxy-reverse": "caddy",
                    "iam": "authelia",
                    "secret": "doppler",
                    "event": "hookdeck",
                    "queue": "rabbitmq",
                    "tracer": "signoz"
                }
                prov_uid = fallbacks.get(svc_key)
                if svc_key == "runner" and prov_uid == "ollama":
                    metal = True
                if svc_key == "network":
                    metal = n.get("hardware", {}).get("headless", False)

            if prov_uid:
                new_providers[svc_key] = {"uid": prov_uid, "metal": metal}

        # Explicitly protect the lifeline for headless WAN nodes
        if n_wan and n.get("hardware", {}).get("headless", False):
            if "network" in new_providers:
                new_providers["network"]["metal"] = True

        n["providers"] = new_providers

    # Prune orphaned nodes that have been completely evicted of planes and services
    profile["nodes"] = [n for n in profile["nodes"] if n.get("planes") or n.get("providers")]

    return profile

  def envInstantiate(self, teardown=False, verbose=False):
    """
    Instantiate the .env file in current directory.
    """
    env_json_path = '.env.json'
    env_template_path = '.env.template'
    env_tmp_path = '.env.tmp'
    env_path = '.env'

    skip_env_prompt = teardown or os.environ.get('OPENCLAW_SKIP_ENV') == '1'

    if teardown:
      for f in [env_path, env_tmp_path]:
        if os.path.exists(f):
          os.remove(f)
      return

    if not os.path.exists(env_template_path):
      return

    env_vars = {}
    if os.path.exists(env_json_path):
      with open(env_json_path, 'r') as f:
        try:
          env_vars = json.load(f)
        except json.JSONDecodeError:
          print(f"Error parsing {env_json_path}. Starting with empty mapping.")

    # Regex matches: KEY=change_me_to_IDENTIFIER[OPTIONAL_DEFAULT] SUFFIX
    # Identifier is optional to handle empty defaults like 'change_me_to_'
    pattern = re.compile(
      r'^(?P<var_name>[^=]+)='
      r'change_me_to_(?P<identifier>[A-Za-z0-9_]*)'
      r'(?:\[(?P<default>.*?)\])?'
      r'(?P<suffix>.*)$')

    # Ensure framework libraries (like newpwd) are in the path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    with open(env_template_path, 'r') as f_in, open(env_tmp_path, 'w') as f_out:
      for line in f_in:
        line_stripped = line.rstrip('\n')
        match = pattern.match(line_stripped)

        if match:
          var_name = match.group('var_name').strip()
          identifier = match.group('identifier')
          explicit_default = match.group('default')
          suffix = match.group('suffix')

          computed_val = ""
          if identifier == "AUTO_PWD":
            computed_val = os.getcwd()
            if explicit_default:
              # We abuse the default syntax to provide a subpath
              computed_val = os.path.abspath(
                os.path.join(computed_val, explicit_default))
          elif identifier == "AUTO_PASSWORD":
            try:
              from newpwd import generate_password
              computed_val = generate_password()
            except ImportError:
              computed_val = "FAILED_TO_GENERATE"
          elif identifier == "AUTO_PASSWORD_SK":
            try:
              from newpwd import generate_password
              computed_val = "sk-" + generate_password()
            except ImportError:
              computed_val = "sk-FAILED_TO_GENERATE"
          elif explicit_default is not None:
            computed_val = explicit_default

          # Prioritize the cached value from .env.json
          if var_name in env_vars and not env_vars[var_name].startswith('change_me_to_'):
            val = env_vars[var_name]
          else:
            if skip_env_prompt:
              # Provide safe dummy values for non-interactive teardown
              if "PORT" in var_name:
                val = "8080"
              elif "VERSION" in var_name:
                val = "latest"
              else:
                val = "TEARDOWN_DUMMY_VALUE"
            else:
              prompt_str = f"Enter value for {var_name}"
              display_default = computed_val if computed_val else identifier
              if display_default:
                prompt_str += f" [{display_default}]"
              prompt_str += ": "

              try:
                user_val = input(prompt_str).strip()
                if user_val:
                  val = user_val
                elif computed_val:
                  val = computed_val
                else:
                  val = ""
              except EOFError:
                 val = computed_val if computed_val else ""

            # Update the cache for future persistence
            env_vars[var_name] = val

            # --- AUTO-PROVISIONING INJECTION FOR WORKSPACE ---
            if var_name == "OPENCLAW_WORKSPACE" and val:
                expanded_val = os.path.expanduser(val)
                if not os.path.exists(expanded_val):
                    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.workspace.template'))
                    if os.path.exists(template_dir):
                        print(f"  [MetaClaw] Auto-provisioning workspace from template into: {expanded_val}")
                        shutil.copytree(template_dir, expanded_val)
                    else:
                        print(f"  [MetaClaw] Creating empty workspace directory: {expanded_val}")
                        os.makedirs(expanded_val)

          out_line = f"{var_name}={val}{suffix}\n"
          f_out.write(out_line)

          if verbose:
            print(f"  {var_name}={val}{suffix}")
        else:
          # Pass non-variable configuration lines straight through
          f_out.write(line_stripped + '\n')

    if not skip_env_prompt:
      with open(env_json_path, 'w') as f:
        json.dump(env_vars, f, indent=2)

    shutil.move(env_tmp_path, env_path)

  def validate(self):
    """
    Analyzes the structure to report missing or empty expected fields,
    printing output hierarchically to guide documentation efforts.
    """
    struct = self.structure()
    services = struct.get('services', {})

    req_svc = ['uid', 'uids', 'name', 'names', 'category', 'purpose']
    req_prov = ['uid', 'name', 'overview', 'details']

    for svc_key in sorted(services):
      print('-' * 80)
      print('Service ' + svc_key)
      svc_val = services[svc_key]
      missing_svc = [f for f in req_svc if not svc_val.get(f)]
      if missing_svc:
        print(f"  WARN: missing/empty fields: {', '.join(missing_svc)}")

      installed = set()
      providers = svc_val.get('providers', {})
      for prov_key in sorted(providers):
        prov_val = providers[prov_key]
        missing_prov = [f for f in req_prov if not prov_val.get(f)]
        print('  Provider ' + prov_key)
        provdir = self.subpath(service=svc_key, provider=prov_key)
        files = os.listdir(provdir)
        if missing_prov:
          print(f"    missing keys: {', '.join(missing_prov)}")
        print("    files: %s" % ', '.join(files))
        if '.env.template' in files:
          installed.add(prov_key)

      if installed:
        print('')
        print('  INSTALLED: %s' % ', '.join(sorted(installed)))

  def destructure(self, struct_data):
    """
    Decomposes a monolithic structure dict into modular JSON fragments
    on the filesystem.
    """
    root_dir = self.rootdir()
    tiers = struct_data.get('tiers', {})
    planes = struct_data.get('planes', {})
    services = struct_data.get('services', {})

    if tiers:
      path = os.path.join(root_dir, '.tiers.json')
      self.saveFile(path, json.dumps(tiers, indent=2), backup=False)

    if planes:
      path = os.path.join(root_dir, '.planes.json')
      self.saveFile(path, json.dumps(planes, indent=2), backup=False)

    svc_dir = os.path.join(root_dir, 'services')
    for svc_key, svc_val in services.items():
      uids = svc_val.get('uids', svc_key)
      target_svc_dir = os.path.join(svc_dir, uids)
      os.makedirs(target_svc_dir, exist_ok=True)

      providers = svc_val.pop('providers', {})
      svc_json_path = os.path.join(target_svc_dir, '.service.json')
      self.saveFile(
        svc_json_path, json.dumps(svc_val, indent=2), backup=False
      )

      for prov_key, prov_val in providers.items():
        target_prov_dir = os.path.join(target_svc_dir, prov_key)
        os.makedirs(target_prov_dir, exist_ok=True)
        prov_json_path = os.path.join(target_prov_dir, '.provider.json')
        self.saveFile(
          prov_json_path, json.dumps(prov_val, indent=2), backup=False
        )

  def rootdir(self):
    """
    Determines the absolute path of the MetaClaw root directory.
    Prioritizes OPENCLAW_ROOT from .env, falling back to the parent of the
    lib directory.
    """
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.dirname(lib_dir)
    env_path = os.path.join(default_root, '.env')

    root_dir = default_root
    if os.path.exists(env_path):
      with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
          line = line.strip()
          if line.startswith('OPENCLAW_ROOT='):
            val = line.split('=', 1)[1].strip()
            # Handle potential quotes in the .env file
            if val.startswith('"') and val.endswith('"'):
              val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
              val = val[1:-1]
            if val and val != 'change_me_to_AUTO_PWD':
              root_dir = val
            break
    return root_dir

  def backupFile(self, filepath):
    """
    Creates a timestamped backup of a file in the .versions directory,
    preserving the original directory structure anchored to the framework root.
    """
    root_dir = self.rootdir()
    versions_dir = os.path.join(root_dir, ".versions")

    abs_filepath = os.path.abspath(filepath)

    try:
      # Replicate the directory tree relative to the framework root
      if abs_filepath.startswith(os.path.abspath(root_dir)):
        rel_path = os.path.relpath(abs_filepath, root_dir)
      else:
        rel_path = os.path.basename(abs_filepath)
    except ValueError:
      rel_path = os.path.basename(abs_filepath)

    dirname = os.path.dirname(rel_path)
    basename = os.path.basename(rel_path)

    target_dir = os.path.join(versions_dir, dirname) if dirname else versions_dir
    os.makedirs(target_dir, exist_ok=True)

    mtime = os.path.getmtime(abs_filepath)
    timestamp = time.strftime('%Y%m%d%H%M%S', time.localtime(mtime))
    backup_name = f"{basename}.{timestamp}"
    backup_path = os.path.join(target_dir, backup_name)

    shutil.move(abs_filepath, backup_path)
    print(f"Backed up {filepath} to {backup_path}")

  def saveFile(self, filepath, new_content, backup=True):
    """
    Checks if a file exists, optionally creates a backup, and writes new content.
    """
    abs_filepath = os.path.abspath(filepath)
    if backup and os.path.exists(abs_filepath):
      self.backupFile(abs_filepath)

    target_dir = os.path.dirname(abs_filepath)
    if target_dir:
      os.makedirs(target_dir, exist_ok=True)

    with open(abs_filepath, 'w', encoding='utf-8') as f:
      f.write(new_content)
    print(f"Wrote updated {filepath}")

# Expose a global instance of the MetaClaw orchestrator library
Inst = MetaClaw()

class Markdown:
  def __init__(self, filepath=None):
    self.filepath = filepath
    self.raw_text = ""
    if self.filepath:
      if not os.path.exists(self.filepath):
        raise FileNotFoundError(f"Error: {self.filepath} not found.")
      with open(self.filepath, 'r', encoding='utf-8') as f:
        self.raw_text = f.read()

  def toHtml(self):
    """
    Parses the Markdown AST and converts it to styled HTML.
    Preprocesses under-indented lists to satisfy the strict 4-space rule.
    """
    text = re.sub(
      r'^[ \t\xa0]{1,3}([-*+]\s)', r'    \1', self.raw_text, flags=re.MULTILINE
    )

    md = md_lib.Markdown(extensions=['tables', 'fenced_code', 'sane_lists'])
    html_body = md.convert(text)

    doc_title = (
      os.path.basename(self.filepath) if self.filepath else 'Generated'
    )

    html_content = (
      f"<!DOCTYPE html>\n"
      f"<html lang=\"en\">\n"
      f"<head>\n"
      f"  <meta charset=\"UTF-8\">\n"
      f"  <meta name=\"viewport\" content=\"width=device-width, "
      f"initial-scale=1.0\">\n"
      f"  <title>{doc_title}</title>\n"
      f"  <style>\n"
      f"    body {{ font-family: -apple-system, BlinkMacSystemFont, "
      f"\"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; "
      f"background-color: #1e1e1e; color: #d4d4d4; max-width: 800px; "
      f"margin: 0 auto; padding: 40px 20px 80vh 20px; line-height: 1.6; }}\n"
      f"    h1 {{ color: #569cd6; border-bottom: 1px solid #333; "
      f"padding-bottom: 10px; scroll-margin-top: 80px; }}\n"
      f"    h2 {{ color: #4ec9b0; margin-top: 30px; border-bottom: 1px "
      f"solid #333; padding-bottom: 5px; scroll-margin-top: 80px; }}\n"
      f"    h3 {{ color: #ce9178; margin-top: 25px; scroll-margin-top: 80px; }}\n"
      f"    .guide {{ background-color: #252526; padding: 20px; "
      f"border-left: 4px solid #4ec9b0; margin-bottom: 30px; }}\n"
      f"    pre {{ background-color: #000; padding: 15px; border-radius: 6px; "
      f"font-family: 'Courier New', Courier, monospace; border: 1px solid "
      f"#333; overflow-x: auto; color: #dcdcaa; }}\n"
      f"    code {{ background-color: #333; padding: 2px 4px; "
      f"border-radius: 4px; color: #ce9178; font-family: monospace; }}\n"
      f"    pre code {{ background-color: transparent; padding: 0; }}\n"
      f"    a {{ color: #569cd6; text-decoration: none; }}\n"
      f"    a:hover {{ text-decoration: underline; }}\n"
      f"    table {{ border-collapse: collapse; width: 100%; "
      f"margin-bottom: 20px; }}\n"
      f"    th, td {{ border: 1px solid #333; padding: 8px; "
      f"text-align: left; }}\n"
      f"    th {{ background-color: #252526; color: #4ec9b0; }}\n"
      f"    ul, ol {{ padding-left: 20px; }}\n"
      f"    li {{ margin-bottom: 5px; }}\n"
      f"  </style>\n"
      f"  <script>\n"
      f"    window.onload = function() {{\n"
      f"      if (window.location.hash.includes('env.vars')) {{\n"
      f"        var banner = document.createElement('div');\n"
      f"        banner.innerHTML = '&#9432; <strong>PRE-FLIGHT CHECK:</strong> This page is informational only. Please review the service overview and return to your terminal to continue.';\n"
      f"        banner.style = 'background-color: #0e639c; color: white; padding: 10px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1000; margin-bottom: 20px; border-radius: 4px;';\n"
      f"        document.body.insertBefore(banner, document.body.firstChild);\n"
      f"      }} else if (window.location.hash.includes('diagnostic-checks')) {{\n"
      f"        var banner = document.createElement('div');\n"
      f"        banner.innerHTML = '&#9432; <strong>BOOT SEQUENCE:</strong> Scroll down to the <strong>Diagnostic Checks</strong> section and verify your terminal output matches the expected results.';\n"
      f"        banner.style = 'background-color: #d7ba7d; color: black; padding: 10px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1000; margin-bottom: 20px; border-radius: 4px;';\n"
      f"        document.body.insertBefore(banner, document.body.firstChild);\n"
      f"        setTimeout(function() {{ var el = document.getElementById('diagnostic-checks'); if(el) el.scrollIntoView({{behavior: \"smooth\"}}); }}, 200);\n"
      f"      }}\n"
      f"    }};\n"
      f"  </script>\n"
      f"</head>\n"
      f"<body>\n"
      f"  {html_body}\n"
      f"</body>\n"
      f"</html>"
    )
    return html_content

  def parse_ast(self):
    """
    Validates the Markdown syntax by parsing it into an AST internally.
    """
    text = re.sub(
      r'^[ \t\xa0]{1,3}([-*+]\s)', r'    \1', self.raw_text, flags=re.MULTILINE
    )
    md = md_lib.Markdown(extensions=['tables', 'fenced_code', 'sane_lists'])
    _ = md.convert(text)
    return True

  def metaclawSetup(self):
    """
    Auto-generates documentation Markdown files from the central registry
    to enforce absolute consistency across the ecosystem.
    """
    struct = Inst.structure()
    services = struct.get('services', {})
    planes = struct.get('planes', {})
    tiers = struct.get('tiers', {})

    categories = {}
    for uid, svc in services.items():
      cat = svc.get('category', 'Uncategorized')
      if cat not in categories:
        categories[cat] = []
      categories[cat].append(svc)

    services_md = [
      "# MetaClaw Service Ecosystem\n",
      "This document serves as the canonical registry for the critical "
      "infrastructure",
      "services that make up the MetaClaw framework.\n"
    ]

    # --- Planes ---
    if planes:
      services_md.append("## Planes\n")
      for p_uid, plane in planes.items():
        services_md.append(f"### {plane['name']} {{#{plane['uid']}}}")
        services_md.append("")

        if 'aka' in plane:
          aka_text = f"* **Aka**: {plane['aka']}"
          services_md.append(
            textwrap.fill(aka_text, width=80, subsequent_indent="  ")
          )

        if 'profile' in plane:
          profile_text = f"* **Profile**: {plane['profile']}"
          services_md.append(
            textwrap.fill(profile_text, width=80, subsequent_indent="  ")
          )

        if 'justification' in plane:
          just_text = f"* **Justification**: {plane['justification']}"
          services_md.append(
            textwrap.fill(just_text, width=80, subsequent_indent="  ")
          )

        if 'services' in plane:
          svcs_text = f"* **Services**: {', '.join(plane['services'])}"
          services_md.append(
            textwrap.fill(svcs_text, width=80, subsequent_indent="  ")
          )

        services_md.append("")

    # --- Tiers ---
    if tiers:
      services_md.append("## Tiers\n")
      for t_uid, tier in tiers.items():
        services_md.append(f"### {tier['name']} {{#{tier['uid']}}}")
        services_md.append("")

        if 'setup' in tier:
          setup_text = f"* **Setup**: {tier['setup']}"
          services_md.append(
            textwrap.fill(setup_text, width=80, subsequent_indent="  ")
          )

        if 'benefit' in tier:
          benefit_text = f"* **Benefit**: {tier['benefit']}"
          services_md.append(
            textwrap.fill(benefit_text, width=80, subsequent_indent="  ")
          )

        services_md.append("")

    # --- Services ---
    if categories:
      services_md.append("## Services\n")
      for cat, svcs in categories.items():
        services_md.append(f"### {cat}\n")
        for svc in svcs:
          services_md.append(f"#### {svc['name']} {{#{svc['uids']}}}")
          services_md.append("")

          services_md.append(f"* **Path**: `services/{svc['uids']}/`")

          purpose_text = f"* **Purpose**: {svc.get('purpose', '')}"
          purpose = textwrap.fill(
            purpose_text, width=80, subsequent_indent="  "
          )
          services_md.append(purpose)

          provider_names = [
            p['name'] for p in svc.get('providers', {}).values()
          ]
          if provider_names:
            options_text = f"* **Options**: {', '.join(provider_names)}."
          else:
            options_text = "* **Options**: None currently defined."

          options = textwrap.fill(
            options_text, width=80, subsequent_indent="  "
          )
          services_md.append(options + "\n")

    Inst.saveFile('docs/SERVICES.md', '\n'.join(services_md), backup=False)

    # Generate the directory index.md files for each service and provider
    for uid, svc in services.items():
      svc_md = [f"# {svc['name']} Overview\n", "## Providers\n"]
      for p_uid, provider in svc.get('providers', {}).items():
        svc_md.append(f"### {provider['name']}")
        if provider.get('overview'):
          overview = textwrap.fill(provider['overview'], width=80)
          svc_md.append(overview + "\n")
        else:
          svc_md.append("\n")

        # Auto-generate the specific provider index.md
        p_md = [f"# {p_uid}: {provider['name']}\n", "## Overview\n"]
        for paragraph in provider.get('details', []):
          p_md.append(textwrap.fill(paragraph, width=80))
          p_md.append("")

        provider_index_path = f"services/{svc['uids']}/{p_uid}/index.md"
        template_path = f"services/{svc['uids']}/{p_uid}/index.template.md"

        if os.path.exists(template_path):
          with open(template_path, 'r', encoding='utf-8') as tf:
            t_md = tf.read()
          if 'diagnostics' in provider and provider['diagnostics'].strip():
            diag_block = f"<h2 id=\"diagnostic-checks\">Diagnostic Checks ({svc.get('uid', 'unknown')} {p_uid})</h2>\n\n{provider['diagnostics']}\n\n"
            if '__DIAGNOSTICS__' in t_md:
              t_md = t_md.replace('__DIAGNOSTICS__', diag_block)
            else:
              t_md += "\n" + diag_block
          Inst.saveFile(provider_index_path, t_md, backup=False)
        else:
          if 'diagnostics' in provider and provider['diagnostics'].strip():
            p_md.append(f"<h2 id=\"diagnostic-checks\">Diagnostic Checks ({svc.get('uid', 'unknown')} {p_uid})</h2>")
            p_md.append(provider['diagnostics'])
            p_md.append("")
          Inst.saveFile(provider_index_path, '\n'.join(p_md), backup=False)

      index_path = f"services/{svc['uids']}/index.md"
      Inst.saveFile(index_path, '\n'.join(svc_md), backup=False)

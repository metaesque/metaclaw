import os
import shutil
import time
import json
import re
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
    reconstructing it from modular JSON fragments. Uses internal caching
    based on file modification timestamps to prevent disk I/O bottlenecks.
    """
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(lib_dir)

    relevant_files = []

    phases_path = os.path.join(root_dir, '.phases.json')
    if os.path.exists(phases_path):
      relevant_files.append(phases_path)

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

          prov_json = os.path.join(prov_folder_path, '.provider.json')
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

    if os.path.exists(phases_path):
      with open(phases_path, 'r', encoding='utf-8') as f:
        struct['phases'] = json.load(f)

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
    phase,
    hardware,
    require_wan,
    order_prefs
  ):
    """
    Analyzes the entire cluster and redistributes service providers based
    on the newly added node. Handles the 'teardown' logic by removing assignments
    from older nodes. Utilizes the order_prefs prioritization matrix to select
    the optimal providers based on Safety, Cost, and Resources.

    Args:
      profile (dict): The current cluster profile loaded from profile.json.
      current_hostname (str): The hostname of the node being profiled.
      phase (int): The target architectural phase (0-4) for this node.
      hardware (dict): The hardware details dictionary for this node.
      require_wan (bool): Whether the node requires remote WAN access.
      order_prefs (list of str): Priority order for provider selection
        (e.g., ['safety', 'cost', 'resources']).

    Returns:
      dict: The updated cluster profile.
    """
    node = next(
      (n for n in profile["nodes"] if n["hostname"] == current_hostname), None
    )
    if not node:
      node = {"hostname": current_hostname}
      profile["nodes"].append(node)

    node["phase"] = phase
    node["hardware"] = hardware

    # Baseline all-in-one defaults
    providers = {
      "gateway": {"uid": "openclaw"},
      "proxy": {"uid": "litellm"},
      "logger": {"uid": "victorialogs"},
      "cache": {"uid": "redis"},
      "memory": {"uid": "postgres"},
      "runner": {"uid": "ollama", "metal": True},
      "sandbox": {"uid": "docker-dood" if hardware["os"] == "Darwin" else "gvisor"},
    }

    if require_wan:
      providers["network"] = {"uid": "tailscale"}

    node["providers"] = providers

    # ============================================================================
    # PHASE REDISTRIBUTION LOGIC (CLUSTER RECONCILIATION)
    # ============================================================================
    if phase == 1:
      # Adding a Phase 1 node obsoletes Phase 0 nodes
      for n in profile["nodes"]:
        if n["phase"] == 0:
          n["providers"] = {} # Mark for full teardown

    elif phase >= 2:
      control_node = next(
        (n for n in profile["nodes"] if n["phase"] == 1), None
      )

      if phase == 2:
        node["providers"] = {
          "runner": {"uid": "vllm" if hardware["vram_gb"] > 20 else "ollama", "metal": True},
        }
        if require_wan:
          node["providers"]["network"] = {"uid": "tailscale"}
        if control_node and "runner" in control_node["providers"]:
          del control_node["providers"]["runner"]

      elif phase == 3:
        node["providers"] = {
          "sandbox": {"uid": "docker-dood" if hardware["os"] == "Darwin" else "gvisor"},
          "ci": {"uid": "woodpecker"},
        }
        if require_wan:
          node["providers"]["network"] = {"uid": "tailscale"}

        # Keep legacy fallback for fetcher/searcher until they are migrated to the matrix
        node["providers"]["fetcher"] = {"uid": "firecrawl"}
        cost_idx = order_prefs.index('cost') if 'cost' in order_prefs else 1
        res_idx = order_prefs.index('resources') if 'resources' in order_prefs else 2
        cost_over_resources = cost_idx < res_idx
        if cost_over_resources:
          node["providers"]["searcher"] = {"uid": "searxng"}
        else:
          node["providers"]["searcher"] = {"uid": "parallelai"}

        if control_node:
          for svc in ["sandbox", "browser", "fetcher", "searcher"]:
            if svc in control_node["providers"]:
              del control_node["providers"][svc]

      elif phase == 4:
        node["providers"] = {
          "memory": {"uid": "postgres"},
          "logger": {"uid": "victorialogs"},
          "vcs": {"uid": "gitea"},
        }
        if require_wan:
          node["providers"]["network"] = {"uid": "tailscale"}
        if control_node:
          control_node["providers"].pop("memory", None)
          control_node["providers"].pop("logger", None)

    # ============================================================================
    # MATRIX RESOLUTION (DYNAMIC OVERRIDES)
    # ============================================================================
    order_str = ",".join(order_prefs)
    struct = self.structure()

    for svc_key, svc_data in struct.get('services', {}).items():
      if 'matrix' in svc_data:
        phase_key = f"phase-{phase}"
        os_key = hardware["os"]
        matrix = svc_data['matrix']

        if phase_key in matrix and os_key in matrix[phase_key] and order_str in matrix[phase_key][os_key]:
          decision = matrix[phase_key][os_key][order_str]
          prov_uid = decision.get("uid")
          metal = decision.get("metal", False)
          why = decision.get("why", "No justification provided.")

          print(f"[Matrix] Selected '{prov_uid}' for {svc_key} (Phase {phase}, {os_key}, {order_str})")
          print(f"         Reason: {why}")

          node["providers"][svc_key] = {
            "uid": prov_uid,
            "metal": metal
          }

    return profile

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
    phases = struct_data.get('phases', {})
    planes = struct_data.get('planes', {})
    services = struct_data.get('services', {})

    if phases:
      path = os.path.join(root_dir, '.phases.json')
      self.saveFile(path, json.dumps(phases, indent=2), backup=False)

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
      f"margin: 0 auto; padding: 40px 20px; line-height: 1.6; }}\n"
      f"    h1 {{ color: #569cd6; border-bottom: 1px solid #333; "
      f"padding-bottom: 10px; }}\n"
      f"    h2 {{ color: #4ec9b0; margin-top: 30px; border-bottom: 1px "
      f"solid #333; padding-bottom: 5px; }}\n"
      f"    h3 {{ color: #ce9178; margin-top: 25px; }}\n"
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
    phases = struct.get('phases', {})

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

    # --- Phases ---
    if phases:
      services_md.append("## Phases\n")
      for ph_uid, phase in phases.items():
        services_md.append(f"### {phase['name']} {{#{phase['uid']}}}")
        services_md.append("")

        if 'setup' in phase:
          setup_text = f"* **Setup**: {phase['setup']}"
          services_md.append(
            textwrap.fill(setup_text, width=80, subsequent_indent="  ")
          )

        if 'benefit' in phase:
          benefit_text = f"* **Benefit**: {phase['benefit']}"
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

        if 'diagnostics' in provider and provider['diagnostics'].strip():
          p_md.append("## Diagnostic Checks\n")
          p_md.append(provider['diagnostics'])
          p_md.append("")

        provider_index_path = f"services/{svc['uids']}/{p_uid}/index.md"
        Inst.saveFile(provider_index_path, '\n'.join(p_md), backup=False)

      index_path = f"services/{svc['uids']}/index.md"
      Inst.saveFile(index_path, '\n'.join(svc_md), backup=False)

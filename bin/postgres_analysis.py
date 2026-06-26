import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

def main():
  parser = argparse.ArgumentParser(description="Analyze LiteLLM Spend Logs from Memory Provider (PostgreSQL)")
  parser.add_argument('--spend', action='store_true', help="Fetch spend logs from the memory service")
  parser.add_argument('--hours', type=int, default=1, help="Hours to look back")
  parser.add_argument('-j', '--json', action='store_true', help="Output in JSON format for agentic parsing")
  args = parser.parse_args()

  # Load framework environment variables
  load_dotenv('.env')
  load_dotenv('services/proxies/litellm/.env')
  load_dotenv('services/memories/postgres/.env')

  # Resolve Database URL, accounting for network aliasing if run from host
  db_url = os.environ.get('ACTIVE_MEMORY_URL_PROXY') or os.environ.get('DATABASE_URL')
  if not db_url:
    db_url = "postgresql://litellm_app:change_me_to_AUTO_PASSWORD@localhost:5432/litellm_db"

  # Replace docker internal network alias with localhost since this runs on the host metal
  db_url = db_url.replace('active-memory', 'localhost')

  # Safely URL-encode the password in case it contains special characters like '@'
  try:
    scheme, rest = db_url.split('://', 1)
    creds, target = rest.rsplit('@', 1)
    user, pwd = creds.split(':', 1)
    # Ensure it's not double-encoded
    safe_pwd = urllib.parse.quote_plus(urllib.parse.unquote_plus(pwd))
    safe_db_url = f"{scheme}://{user}:{safe_pwd}@{target}"
  except ValueError:
    safe_db_url = db_url

  try:
    conn = psycopg2.connect(safe_db_url)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  except Exception as e:
    print(f"FATAL: Could not connect to Memory Provider (Postgres) at {safe_db_url}\nError: {e}")
    sys.exit(1)

  if args.spend:
    # Use timezone-aware UTC datetimes to prevent Python 3.12+ DeprecationWarnings
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    # LiteLLM tables are sometimes quoted with exact casing depending on version
    try:
      query = """
        SELECT "startTime", "model", "prompt_tokens", "completion_tokens", "total_tokens", "spend"
        FROM "LiteLLM_SpendLogs"
        WHERE "startTime" >= %s
        ORDER BY "startTime" DESC
      """
      cursor.execute(query, (time_threshold,))
      rows = cursor.fetchall()
    except psycopg2.errors.UndefinedTable:
      conn.rollback()
      # Fallback to lowercase schema
      query = """
        SELECT "startTime", model, prompt_tokens, completion_tokens, total_tokens, spend
        FROM litellm_spendlogs
        WHERE "startTime" >= %s
        ORDER BY "startTime" DESC
      """
      cursor.execute(query, (time_threshold,))
      rows = cursor.fetchall()

    if args.json:
      data = [dict(r) for r in rows]
      for d in data:
        if isinstance(d.get('startTime'), datetime):
          d['startTime'] = d['startTime'].isoformat()
        if d.get('spend') is not None:
          d['spend'] = float(d['spend'])
      print(json.dumps(data, indent=2))
    else:
      print(f"\n--- LiteLLM Proxy Service Spend Logs (Last {args.hours} Hours) ---\n")
      if not rows:
        print("No logs found.")
      else:
        header = f"{'startTime':<25} | {'model':<30} | {'prompt_tokens':<13} | {'completion_tokens':<17} | {'total_tokens':<12} | {'spend'}"
        print(header)
        print("-" * len(header))
        for r in rows:
          st = str(r['startTime'])[:23]
          print(f"{st:<25} | {str(r['model']):<30} | {str(r['prompt_tokens']):<13} | {str(r['completion_tokens']):<17} | {str(r['total_tokens']):<12} | {str(r['spend'])}")

  cursor.close()
  conn.close()

if __name__ == "__main__":
  main()

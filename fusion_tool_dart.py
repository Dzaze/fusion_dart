#!/usr/bin/env python3
import os
import re
import logging
import argparse
import hashlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

MARKER_BEGIN = "/* BEGIN FILE: {path} */"
MARKER_END   = "/* END FILE: {path} */"
DEFAULT_SKIP_DIRS = {".git", "build", ".dart_tool", ".idea"}

# ── helpers ────────────────────────────────────────────────────────────────────

def _file_hash(path: str) -> str:
    return hashlib.md5(open(path, "rb").read()).hexdigest()

def _collect_files(project_dir: str, extensions: tuple[str, ...], skip_dirs: set[str]):
    """Retourne la liste triée des fichiers correspondants."""
    results = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = sorted(d for d in dirs if d not in skip_dirs)   # tri + exclusion
        for file in sorted(files):
            if any(file.endswith(ext) for ext in extensions):
                results.append(os.path.join(root, file))
    return results

# ── merge ──────────────────────────────────────────────────────────────────────

def merge_files(
    project_dir: str,
    output_file: str,
    extensions: tuple[str, ...] = (".dart",),
    skip_dirs: set[str] = DEFAULT_SKIP_DIRS,
    force: bool = False,
    dry_run: bool = False,
):
    if os.path.exists(output_file) and not force:
        log.warning("'%s' existe déjà. Utilisez --force pour écraser.", output_file)
        return

    files = _collect_files(project_dir, extensions, skip_dirs)
    if not files:
        log.warning("Aucun fichier trouvé dans '%s' avec les extensions %s.", project_dir, extensions)
        return

    log.info("%d fichier(s) trouvé(s).", len(files))

    if dry_run:
        for f in files:
            log.info("[dry-run] Inclurait : %s", os.path.relpath(f, project_dir))
        return

    with open(output_file, "w", encoding="utf-8") as out_f:
        for file_path in files:
            rel_path = os.path.relpath(file_path, project_dir)
            try:
                content = open(file_path, "r", encoding="utf-8").read()
            except (OSError, UnicodeDecodeError) as e:
                log.error("Impossible de lire '%s' : %s — ignoré.", file_path, e)
                continue
            out_f.write(MARKER_BEGIN.format(path=rel_path) + "\n")
            out_f.write(content)
            out_f.write("\n" + MARKER_END.format(path=rel_path) + "\n\n")

    log.info("Fusion terminée → %s", output_file)

# ── split ──────────────────────────────────────────────────────────────────────

PATTERN = re.compile(
    r'/\*\s*BEGIN FILE:\s*(.*?)\s*\*/\n(.*?)\n/\*\s*END FILE:\s*\1\s*\*/',
    re.DOTALL,
)

def split_file(
    super_file: str,
    project_dir: str,
    force: bool = False,
    dry_run: bool = False,
):
    try:
        content = open(super_file, "r", encoding="utf-8").read()
    except OSError as e:
        log.error("Impossible de lire '%s' : %s", super_file, e)
        return

    matches = list(PATTERN.finditer(content))
    if not matches:
        log.warning("Aucun bloc trouvé dans '%s'.", super_file)
        return

    log.info("%d fichier(s) à réinjecter.", len(matches))

    for match in matches:
        rel_path    = match.group(1).strip()
        new_content = match.group(2)
        target_file = os.path.join(project_dir, rel_path)

        if dry_run:
            log.info("[dry-run] Réinjecterait : %s", target_file)
            continue

        # Sauter si le contenu n'a pas changé
        if os.path.exists(target_file):
            if not force and open(target_file, "r", encoding="utf-8").read() == new_content:
                log.info("Inchangé, ignoré : %s", rel_path)
                continue

        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        try:
            open(target_file, "w", encoding="utf-8").write(new_content)
            log.info("Réinjecté : %s", target_file)
        except OSError as e:
            log.error("Écriture impossible pour '%s' : %s", target_file, e)

    log.info("Réinjection terminée.")

# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description="Fusion / réinjection de fichiers sources")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    parser.add_argument("--force",   action="store_true", help="Écrase sans confirmation")
    parser.add_argument("--extensions", nargs="+", default=[".dart"],
                        metavar="EXT", help="Extensions à traiter (défaut: .dart)")
    parser.add_argument("--skip-dirs", nargs="+", default=list(DEFAULT_SKIP_DIRS),
                        metavar="DIR", help="Dossiers à exclure")

    sub = parser.add_subparsers(dest="command")

    m = sub.add_parser("merge", help="Fusionner les fichiers dans un super fichier")
    m.add_argument("output_file", nargs="?", default="merged_output.dart")
    m.add_argument("--project_dir", default=script_dir)

    s = sub.add_parser("split", help="Réinjecter depuis le super fichier")
    s.add_argument("super_file")
    s.add_argument("--project_dir", default=script_dir)

    args = parser.parse_args()

    if args.command == "merge":
        merge_files(
            args.project_dir, args.output_file,
            extensions=tuple(args.extensions),
            skip_dirs=set(args.skip_dirs),
            force=args.force, dry_run=args.dry_run,
        )
    elif args.command == "split":
        split_file(
            args.super_file, args.project_dir,
            force=args.force, dry_run=args.dry_run,
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import argparse
import re

def merge_files(project_dir, output_file):
    """
    Parcourt le dossier du projet et fusionne tous les fichiers .dart
    dans un seul fichier en insérant des marqueurs pour chaque fichier.
    """
    with open(output_file, "w", encoding="utf-8") as out_f:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith(".dart"):
                    file_path = os.path.join(root, file)
                    # Calcul du chemin relatif pour retrouver le fichier plus tard
                    rel_path = os.path.relpath(file_path, project_dir)
                    out_f.write(f"/* BEGIN FILE: {rel_path} */\n")
                    with open(file_path, "r", encoding="utf-8") as in_f:
                        content = in_f.read()
                        out_f.write(content)
                    out_f.write(f"\n/* END FILE: {rel_path} */\n\n")
    print(f"Fusion terminée. Super fichier créé : {output_file}")

def split_file(super_file, project_dir):
    """
    Lit le super fichier et extrait les contenus de chaque fichier en
    se basant sur les marqueurs pour réinjecter les modifications dans
    les fichiers d'origine.
    """
    with open(super_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Expression régulière pour capturer les blocs entre BEGIN et END
    pattern = re.compile(
        r'/\*\s*BEGIN FILE:\s*(.*?)\s*\*/\n(.*?)\n/\*\s*END FILE:\s*\1\s*\*/',
        re.DOTALL
    )
    matches = pattern.finditer(content)

    for match in matches:
        rel_path = match.group(1).strip()
        file_content = match.group(2)
        target_file = os.path.join(project_dir, rel_path)
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        with open(target_file, "w", encoding="utf-8") as out_f:
            out_f.write(file_content)
        print(f"Réinjecté : {target_file}")

    print("Réinjection terminée.")

def main():
    # Récupère le répertoire où se trouve le script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Outil de fusion et réinjection pour fichiers Dart"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # Commande pour la fusion
    parser_merge = subparsers.add_parser("merge", help="Fusionner les fichiers Dart dans un super fichier")
    parser_merge.add_argument("output_file", help="Chemin du super fichier de sortie")
    parser_merge.add_argument(
        "--project_dir",
        default=script_dir,
        help="Chemin du dossier du projet (défaut: répertoire du script)"
    )

    # Commande pour la réinjection
    parser_split = subparsers.add_parser("split", help="Réinjecter les fichiers modifiés à partir du super fichier")
    parser_split.add_argument("super_file", help="Chemin du super fichier modifié")
    parser_split.add_argument(
        "--project_dir",
        default=script_dir,
        help="Chemin du dossier du projet (défaut: répertoire du script)"
    )

    args = parser.parse_args()

    if args.command == "merge":
        merge_files(args.project_dir, args.output_file)
    elif args.command == "split":
        split_file(args.super_file, args.project_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

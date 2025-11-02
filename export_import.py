import csv
import datetime
import logging
from typing import List
from data_manager import Flashcard

def export_flashcards_to_csv(flashcards: List[Flashcard], filepath: str) -> bool:
    """
    Exportiert Flashcards in eine CSV-Datei.

    Args:
        flashcards (List[Flashcard]): Liste der Flashcards, die exportiert werden sollen.
        filepath (str): Pfad zur Export-CSV-Datei.

    Returns:
        bool: True bei Erfolg, False bei Fehler.
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            fieldnames = [
                "Question", "Answer", "Category", "Subcategory", "Tags",
                "Interval", "Ease Factor", "Repetitions", "Last Reviewed",
                "Next Review", "Consecutive Correct", "Success Count"
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for fc in flashcards:
                writer.writerow({
                    "Question": fc.question,
                    "Answer": fc.answer,
                    "Category": fc.category,
                    "Subcategory": fc.subcategory,
                    "Tags": ", ".join(fc.tags),
                    "Interval": fc.interval,
                    "Ease Factor": fc.ease_factor,
                    "Repetitions": fc.repetitions,
                    "Last Reviewed": fc.last_reviewed,
                    "Next Review": fc.next_review,
                    "Consecutive Correct": fc.consecutive_correct,
                    "Success Count": fc.success_count
                })
        logging.info(f"Flashcards erfolgreich nach {filepath} exportiert.")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Exportieren der Flashcards nach CSV: {e}")
        return False

def import_flashcards_from_csv(filepath: str) -> List[Flashcard]:
    """
    Importiert Flashcards aus einer CSV-Datei.

    Args:
        filepath (str): Pfad zur Import-CSV-Datei.

    Returns:
        List[Flashcard]: Liste der erfolgreich importierten Flashcards.
    """
    imported_flashcards = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_number, row in enumerate(reader, start=2):  # Start bei 2 wegen Header
                try:
                    tags = [tag.strip() for tag in row.get("Tags", "").split(',') if tag.strip()]
                    flashcard = Flashcard(
                        question=row["Question"],
                        answer=row["Answer"],
                        category=row["Category"],
                        subcategory=row["Subcategory"],
                        tags=tags,
                        interval=int(row["Interval"]) if row.get("Interval") else 1,
                        ease_factor=float(row["Ease Factor"]) if row.get("Ease Factor") else 2.5,
                        repetitions=int(row["Repetitions"]) if row.get("Repetitions") else 0,
                        last_reviewed=row.get("Last Reviewed", datetime.date.today().isoformat()),
                        next_review=row.get("Next Review", (datetime.date.today() + datetime.timedelta(days=1)).isoformat()),
                        consecutive_correct=int(row["Consecutive Correct"]) if row.get("Consecutive Correct") else 0,
                        success_count=int(row["Success Count"]) if row.get("Success Count") else 0
                    )
                    imported_flashcards.append(flashcard)
                except KeyError as ke:
                    logging.warning(f"Fehlendes Feld {ke} in Zeile {row_number}. Zeile übersprungen.")
                except ValueError as ve:
                    logging.warning(f"Ungültige Datentypen in Zeile {row_number}: {ve}. Zeile übersprungen.")
        logging.info(f"{len(imported_flashcards)} Flashcards erfolgreich aus {filepath} importiert.")
        return imported_flashcards
    except FileNotFoundError:
        logging.error(f"Importdatei {filepath} nicht gefunden.")
        return []
    except Exception as e:
        logging.error(f"Fehler beim Importieren der Flashcards aus CSV: {e}")
        return []

# Beispiel für die Verwendung
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("export_import.log"),
            logging.StreamHandler()
        ]
    )
    
    # Beispiel Flashcards zum Exportieren
    sample_flashcards = [
        Flashcard(
            question="Was ist die Hauptstadt von Frankreich?",
            answer="Paris",
            category="Geographie",
            subcategory="Hauptstädte",
            tags=["Europa", "Politik"],
            interval=1,
            ease_factor=2.5,
            repetitions=0,
            last_reviewed=datetime.date.today().isoformat(),
            next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
            consecutive_correct=0,
            success_count=0
        ),
        Flashcard(
            question="Was ist die chemische Formel von Wasser?",
            answer="HÃÂ¢Ã¢ÂÂÃ¢ÂÂO",
            category="Chemie",
            subcategory="Grundlagen",
            tags=["Wissenschaft", "Chemie"],
            interval=1,
            ease_factor=2.5,
            repetitions=0,
            last_reviewed=datetime.date.today().isoformat(),
            next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
            consecutive_correct=0,
            success_count=0
        )
    ]
    
    # Exportiere die Beispiel Flashcards
    export_success = export_flashcards_to_csv(sample_flashcards, 'exported_flashcards.csv')
    
    # Importiere die Flashcards aus der exportierten Datei
    if export_success:
        imported_flashcards = import_flashcards_from_csv('exported_flashcards.csv')
        print(f"Importierte Flashcards: {len(imported_flashcards)}")

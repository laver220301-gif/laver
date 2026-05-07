#!/usr/bin/env python3
"""
Программа для конвертации PDF файлов в формат Markdown.

Использует библиотеку pymupdf4llm для извлечения текста и форматирования.

Установка зависимостей:
    pip install pymupdf4llm

Примеры использования:
    # Конвертировать один файл
    python pdf2md.py input.pdf output.md
    
    # Конвертировать с выводом в консоль
    python pdf2md.py input.pdf
    
    # Конвертировать все PDF в папке
    python pdf2md.py ./documents/ --output-dir ./markdown/
    
    # С опциями
    python pdf2md.py input.pdf output.md --show-progress --page-range 1-5
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("Ошибка: библиотека pymupdf4llm не установлена.")
    print("Установите её командой: pip install pymupdf4llm")
    sys.exit(1)


def convert_pdf_to_markdown(
    input_path: str,
    output_path: str | None = None,
    page_range: tuple[int | None, int | None] = (None, None),
    show_progress: bool = False,
) -> str:
    """
    Конвертирует PDF файл в Markdown.

    Args:
        input_path: Путь к входному PDF файлу.
        output_path: Путь для сохранения Markdown файла (опционально).
        page_range: Диапазон страниц для конвертации (start, end).
                   Если None, конвертируются все страницы.
        show_progress: Показывать индикатор прогресса.

    Returns:
        Строка с содержимым Markdown.
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")
    
    if not input_file.suffix.lower() == ".pdf":
        raise ValueError(f"Ожидается PDF файл, получен: {input_file.suffix}")

    # Определяем диапазон страниц
    pages_param = None
    if any(page_range):
        start, end = page_range
        if start is not None and end is not None:
            pages_param = list(range(start - 1, end))  # pymupdf использует 0-based индекс
        elif start is not None:
            pages_param = list(range(start - 1, None))
        elif end is not None:
            pages_param = list(range(0, end))

    # Конвертация
    markdown_text = pymupdf4llm.to_markdown(
        input_file,
        pages=pages_param,
        show_progress=show_progress,
    )

    # Сохранение в файл, если указан путь
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown_text, encoding="utf-8")
        print(f"✓ Файл сохранён: {output_path}")

    return markdown_text


def convert_directory(
    input_dir: str,
    output_dir: str,
    show_progress: bool = False,
) -> None:
    """
    Конвертирует все PDF файлы в директории.

    Args:
        input_dir: Путь к директории с PDF файлами.
        output_dir: Путь к директории для сохранения Markdown файлов.
        show_progress: Показывать индикатор прогресса.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"Директория не найдена: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.PDF"))
    
    if not pdf_files:
        print(f"В директории '{input_dir}' не найдено PDF файлов.")
        return

    print(f"Найдено PDF файлов: {len(pdf_files)}")
    
    for pdf_file in pdf_files:
        md_filename = pdf_file.stem + ".md"
        md_path = output_path / md_filename
        
        try:
            print(f"\nКонвертация: {pdf_file.name}")
            convert_pdf_to_markdown(
                str(pdf_file),
                str(md_path),
                show_progress=show_progress,
            )
        except Exception as e:
            print(f"✗ Ошибка при конвертации {pdf_file.name}: {e}")

    print(f"\n✓ Конвертация завершена. Файлы сохранены в: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Конвертация PDF файлов в формат Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "input",
        help="Путь к PDF файлу или директории с PDF файлами",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Путь для сохранения MD файла (или директория для пакетной конвертации)",
    )
    parser.add_argument(
        "--page-range",
        type=str,
        default=None,
        help="Диапазон страниц в формате 'start-end' (например, '1-5'). "
             "Работает только для одиночных файлов.",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Показывать индикатор прогресса конвертации",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Вывод результата в стандартный поток вывода (консоль)",
    )

    args = parser.parse_args()

    # Проверка входного пути
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Ошибка: Путь не найден: {args.input}")
        sys.exit(1)

    # Парсинг диапазона страниц
    page_range = (None, None)
    if args.page_range:
        try:
            parts = args.page_range.split("-")
            if len(parts) == 2:
                page_range = (int(parts[0]), int(parts[1]))
            elif len(parts) == 1:
                page_range = (int(parts[0]), None)
            else:
                raise ValueError
        except ValueError:
            print(f"Ошибка: Неверный формат диапазона страниц: {args.page_range}")
            print("Используйте формат 'start-end' (например, '1-5')")
            sys.exit(1)

    # Конвертация файла или директории
    try:
        if input_path.is_dir():
            # Пакетная конвертация директории
            if not args.output:
                print("Ошибка: Для конвертации директории необходимо указать выходную директорию.")
                print("Пример: python pdf2md.py ./pdf_folder/ ./md_output/")
                sys.exit(1)
            
            convert_directory(
                args.input,
                args.output,
                show_progress=args.show_progress,
            )
        else:
            # Конвертация одиночного файла
            output_path = args.output
            
            if args.stdout or not output_path:
                # Вывод в консоль
                markdown_text = convert_pdf_to_markdown(
                    args.input,
                    output_path=None,
                    page_range=page_range,
                    show_progress=args.show_progress,
                )
                print(markdown_text)
            else:
                # Сохранение в файл
                convert_pdf_to_markdown(
                    args.input,
                    output_path,
                    page_range=page_range,
                    show_progress=args.show_progress,
                )
                
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

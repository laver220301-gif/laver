"""
PDF to Markdown Converter with GUI
Современный интерфейс для конвертации PDF файлов в Markdown
Работает на Windows, macOS и Linux

Установка зависимостей:
pip install pymupdf4llm customtkinter packaging

Запуск:
python pdf2md_gui.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from pathlib import Path
import threading
import os
import sys

try:
    import pymupdf4llm
except ImportError:
    print("Установите pymupdf4llm: pip install pymupdf4llm")
    sys.exit(1)


class PDFToMarkdownConverter(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Настройка окна
        self.title("PDF в Markdown Конвертер")
        self.geometry("700x550")
        self.minsize(600, 500)
        
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Переменные
        self.pdf_files = []
        self.output_folder = ""
        self.is_converting = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """Создание элементов интерфейса"""
        
        # Главный контейнер с отступами
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="📄 PDF в Markdown Конвертер",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(10, 20))
        
        # Секция выбора файлов
        self.files_frame = ctk.CTkFrame(self.main_frame)
        self.files_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок секции
        self.files_title = ctk.CTkLabel(
            self.files_frame,
            text="Выбранные PDF файлы:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.files_title.pack(padx=10, pady=(10, 5), anchor="w")
        
        # Список файлов
        self.files_listbox = tk.Listbox(
            self.files_frame,
            font=("Arial", 11),
            selectbackground="#3B8ED0",
            selectforeground="white",
            bg="#2B2B2B",
            fg="white",
            borderwidth=0,
            highlightthickness=0
        )
        self.files_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Кнопки управления файлами
        self.files_buttons_frame = ctk.CTkFrame(self.files_frame, fg_color="transparent")
        self.files_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.add_file_btn = ctk.CTkButton(
            self.files_buttons_frame,
            text="➕ Добавить файлы",
            command=self.add_files,
            width=150
        )
        self.add_file_btn.pack(side="left", padx=5)
        
        self.remove_file_btn = ctk.CTkButton(
            self.files_buttons_frame,
            text="➖ Удалить выбранный",
            command=self.remove_selected_file,
            width=150
        )
        self.remove_file_btn.pack(side="left", padx=5)
        
        self.clear_all_btn = ctk.CTkButton(
            self.files_buttons_frame,
            text="🗑️ Очистить всё",
            command=self.clear_all_files,
            width=120,
            fg_color="#D32F2F"
        )
        self.clear_all_btn.pack(side="right", padx=5)
        
        # Секция настроек вывода
        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.pack(fill="x", padx=10, pady=10)
        
        # Путь к папке вывода
        self.output_label = ctk.CTkLabel(
            self.output_frame,
            text="Папка для сохранения:",
            font=ctk.CTkFont(size=14)
        )
        self.output_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.output_path_var = tk.StringVar(value="./output")
        self.output_entry = ctk.CTkEntry(
            self.output_frame,
            textvariable=self.output_path_var,
            width=400
        )
        self.output_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        self.browse_btn = ctk.CTkButton(
            self.output_frame,
            text="📁 Обзор",
            command=self.browse_output_folder,
            width=100
        )
        self.browse_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Настройки конвертации
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Чекбоксы настроек
        self.show_progress_var = tk.BooleanVar(value=True)
        self.progress_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Показывать прогресс",
            variable=self.show_progress_var
        )
        self.progress_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.open_after_var = tk.BooleanVar(value=False)
        self.open_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Открыть папку после конвертации",
            variable=self.open_after_var
        )
        self.open_checkbox.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Прогресс бар
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=10, pady=5)
        
        # Кнопка конвертации
        self.convert_btn = ctk.CTkButton(
            self.main_frame,
            text="🚀 Начать конвертацию",
            command=self.start_conversion,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.convert_btn.pack(fill="x", padx=10, pady=(10, 20))
        
        # Информация
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="💡 Поддерживаются одиночные файлы и пакетная обработка",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.info_label.pack(pady=(0, 10))
        
    def add_files(self):
        """Добавление PDF файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите PDF файлы",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")]
        )
        
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                self.files_listbox.insert(tk.END, Path(file).name)
                
        self.update_status(f"Добавлено файлов: {len(self.pdf_files)}")
        
    def remove_selected_file(self):
        """Удаление выбранного файла"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            del self.pdf_files[index]
            self.files_listbox.delete(index)
            self.update_status(f"Файл удалён. Осталось: {len(self.pdf_files)}")
            
    def clear_all_files(self):
        """Очистка всех файлов"""
        self.pdf_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.update_status("Список файлов очищен")
        
    def browse_output_folder(self):
        """Выбор папки для сохранения"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.output_path_var.set(folder)
            self.output_folder = folder
            
    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.configure(text=message)
        
    def start_conversion(self):
        """Запуск процесса конвертации"""
        if not self.pdf_files:
            messagebox.showwarning("Внимание", "Выберите хотя бы один PDF файл!")
            return
            
        output_folder = self.output_path_var.get()
        if not output_folder:
            messagebox.showwarning("Внимание", "Укажите папку для сохранения!")
            return
            
        # Создание папки если не существует
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="⏳ Конвертация...")
        self.progress_bar.set(0)
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.convert_files, args=(output_folder,))
        thread.daemon = True
        thread.start()
        
    def convert_files(self, output_folder):
        """Конвертация файлов"""
        total_files = len(self.pdf_files)
        
        try:
            for i, pdf_file in enumerate(self.pdf_files, 1):
                if not self.is_converting:
                    break
                    
                # Обновление прогресса
                progress = (i - 1) / total_files
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                self.after(0, lambda f=Path(pdf_file).name, i=i: 
                          self.update_status(f"Конвертация {i}/{total_files}: {f}"))
                
                # Конвертация
                md_text = pymupdf4llm.to_markdown(pdf_file)
                
                # Сохранение
                output_file = Path(output_folder) / f"{Path(pdf_file).stem}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(md_text)
                    
            # Завершение
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.update_status(f"✅ Готово! Конвертировано файлов: {total_files}"))
            self.after(0, lambda: messagebox.showinfo("Успех", 
                       f"Конвертация завершена!\n\nФайлы сохранены в:\n{output_folder}"))
            
            # Открытие папки
            if self.open_after_var.get():
                self.after(0, lambda: os.startfile(output_folder) if os.name == 'nt' 
                          else os.system(f'open "{output_folder}"' if os.name == 'darwin' 
                                        else f'xdg-open "{output_folder}"'))
                          
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка конвертации:\n{str(e)}"))
            self.after(0, lambda: self.update_status("❌ Ошибка конвертации"))
            
        finally:
            self.is_converting = False
            self.after(0, lambda: self.convert_btn.configure(state="normal", text="🚀 Начать конвертацию"))
            
    def on_closing(self):
        """Обработка закрытия окна"""
        if self.is_converting:
            if messagebox.askokcancel("Выход", "Конвертация ещё идёт. Прервать?"):
                self.is_converting = False
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = PDFToMarkdownConverter()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

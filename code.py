import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, simpledialog
import os
import mmap

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Mogd Editor")
        self.file_path = None
        self.unsaved_changes = False
        self.max_file_size = 90 * 1024 * 1024 * 1024  # 90 ГБ в байтах

        # --- Меню ---
        self.menu_bar = tk.Menu(root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Новый", command=self.new_file, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Открыть...", command=self.open_file, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Сохранить как...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=self.exit_editor, accelerator="Ctrl+Q")
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Вырезать", command=self.cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Копировать", command=self.copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Вставить", command=self.paste, accelerator="Ctrl+V")
        self.edit_menu.add_command(label="Удалить", command=self.delete, accelerator="Delete")
        self.edit_menu.add_command(label="Выделить всё", command=self.select_all, accelerator="Ctrl+A")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Найти...", command=self.find_text, accelerator="Ctrl+F")
        self.edit_menu.add_command(label="Заменить...", command=self.replace_text, accelerator="Ctrl+H")
        self.menu_bar.add_cascade(label="Правка", menu=self.edit_menu)

        self.root.config(menu=self.menu_bar)

        # --- Текстовая область ---
        self.text_area = scrolledtext.ScrolledText(root, undo=True)
        self.text_area.pack(expand=True, fill='both')
        self.text_area.bind("<Key>", self.set_unsaved_changes)

        # --- Привязка горячих клавиш ---
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda event: self.save_file_as())
        self.root.bind("<Control-q>", lambda event: self.exit_editor())
        self.root.bind("<Control-z>", lambda event: self.undo())
        self.root.bind("<Control-y>", lambda event: self.redo())
        self.root.bind("<Control-x>", lambda event: self.cut())
        self.root.bind("<Control-c>", lambda event: self.copy())
        self.root.bind("<Control-v>", lambda event: self.paste())
        self.root.bind("<Delete>", lambda event: self.delete())
        self.root.bind("<Control-a>", lambda event: self.select_all())
        self.root.bind("<Control-f>", lambda event: self.find_text())
        self.root.bind("<Control-h>", lambda event: self.replace_text())


        # --- Строка состояния ---
        self.status_bar = tk.Label(root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar()
        self.text_area.bind("<<Modified>>", self.update_status_bar)

    # --- Методы для меню "Файл" ---

    def new_file(self):
        if self.unsaved_changes:
            if not self.confirm_discard_changes():
                return
        self.text_area.delete(1.0, tk.END)
        self.file_path = None
        self.root.title("Mogd Editor")
        self.unsaved_changes = False
        self.update_status_bar()

    def open_file(self):
        if self.unsaved_changes:
            if not self.confirm_discard_changes():
                return

        filepath = filedialog.askopenfilename(
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filepath:
            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                messagebox.showerror("Ошибка", f"Файл слишком большой. Максимальный размер: {self.max_file_size / (1024 * 1024 * 1024):.2f} GB") # Изменено на ГБ
                return

            try:
                with open(filepath, "r+b") as f:
                    with mmap.mmap(f.fileno(), 0) as mm:
                        try:
                            content = mm.read().decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                content = mm.read().decode('windows-1251')
                            except UnicodeDecodeError:
                                messagebox.showerror("Ошибка", "Не удалось определить кодировку файла.")
                                return

                        self.text_area.delete(1.0, tk.END)
                        self.text_area.insert(1.0, content)
                        self.file_path = filepath
                        self.root.title(f"Mogd Editor - {os.path.basename(filepath)}")
                        self.unsaved_changes = False
                        self.update_status_bar()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")
    def save_file(self):
        if self.file_path:
            try:
                with open(self.file_path, "w", encoding="utf-8") as file:
                    content = self.text_area.get(1.0, tk.END)
                    file.write(content)
                self.unsaved_changes = False
                self.update_status_bar()
                self.root.title(f"Mogd Editor - {os.path.basename(self.file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    content = self.text_area.get(1.0, tk.END)
                    file.write(content)
                self.file_path = filepath
                self.unsaved_changes = False
                self.update_status_bar()
                self.root.title(f"Mogd Editor - {os.path.basename(filepath)}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def exit_editor(self):
         if self.unsaved_changes:
            if not self.confirm_discard_changes():
                return
         self.root.quit()

    def confirm_discard_changes(self):
        response = messagebox.askyesnocancel("Несохраненные изменения", "Есть несохраненные изменения. Сохранить?")
        if response is None:
            return False
        elif response is True:
            self.save_file()
            return True
        else:
             return True

    def set_unsaved_changes(self, event=None):
        if self.text_area.edit_modified():
            self.unsaved_changes = True
            self.text_area.edit_modified(False)
            self.update_status_bar()


    # --- Методы для меню "Правка" ---
    def undo(self):
        try:
            self.text_area.edit_undo()
            self.update_status_bar()
        except tk.TclError:
            pass
    def redo(self):
        try:
            self.text_area.edit_redo()
            self.update_status_bar()
        except tk.TclError:
            pass

    def cut(self):
        self.text_area.event_generate("<<Cut>>")
        self.update_status_bar()
    def copy(self):
        self.text_area.event_generate("<<Copy>>")
        self.update_status_bar()

    def paste(self):
        self.text_area.event_generate("<<Paste>>")
        self.update_status_bar()

    def delete(self):
        try:
            self.text_area.delete("sel.first", "sel.last")
            self.update_status_bar()
        except tk.TclError:
           pass

    def select_all(self):
        self.text_area.tag_add("sel", "1.0", "end")
        self.update_status_bar()

    def find_text(self):
       target = simpledialog.askstring("Поиск", "Что искать:")
       if target:
          start_index = self.text_area.search(target, "1.0", stopindex=tk.END)
          if start_index:
             end_index = f"{start_index}+{len(target)}c"
             self.text_area.tag_remove("sel", "1.0", tk.END)
             self.text_area.tag_add("sel", start_index, end_index)
             self.text_area.mark_set("insert", end_index)
             self.text_area.see(start_index)
             self.update_status_bar()
          else:
            messagebox.showinfo("Поиск", "Совпадений не найдено.")

    def replace_text(self):
        find_what = simpledialog.askstring("Найти", "Что искать:")
        if find_what:
            replace_with = simpledialog.askstring("Заменить", "На что заменить:")
            if replace_with is not None:
                start_index = "1.0"
                while True:
                    start_index = self.text_area.search(find_what, start_index, stopindex=tk.END)
                    if not start_index:
                        break
                    end_index = f"{start_index}+{len(find_what)}c"
                    self.text_area.delete(start_index, end_index)
                    self.text_area.insert(start_index, replace_with)
                    start_index = f"{start_index}+{len(replace_with)}c"
                self.update_status_bar()

    def update_status_bar(self, event=None):
        if self.unsaved_changes:
            status = "Не сохранено"
        else:
            status = "Сохранено"

        row, col = self.text_area.index(tk.INSERT).split(".")
        status += f" | Строка: {int(row)}, Столбец: {int(col) + 1}"
        self.status_bar.config(text=status)

# --- Запуск ---
root = tk.Tk()
editor = TextEditor(root)
root.mainloop()
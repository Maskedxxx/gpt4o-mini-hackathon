import os

def print_tree(start_path, exclude_files=None, indent=""):
    """
    Рекурсивно обходит директории и файлы, выводя дерево проекта.
    
    :param start_path: Начальный путь проекта.
    :param exclude_files: Список файлов и папок, которые нужно исключить.
    :param indent: Отступ для текущего уровня вложенности.
    """
    if exclude_files is None:
        exclude_files = []

    try:
        items = [item for item in os.listdir(start_path) if item not in exclude_files]
    except PermissionError:
        print(indent + "[Доступ запрещен]")
        return

    items.sort()
    for i, item in enumerate(items):
        path = os.path.join(start_path, item)
        is_last = i == len(items) - 1

        if os.path.isdir(path):
            print(f"{indent}{'└── ' if is_last else '├── '}{item}/")
            print_tree(path, exclude_files, indent + ("    " if is_last else "│   "))
        else:
            print(f"{indent}{'└── ' if is_last else '├── '}{item}")

if __name__ == "__main__":
    # Укажите путь к вашему проекту
    project_path = "***"  # Замените на путь к вашему проекту

    # Укажите файлы и папки, которые нужно исключить
    exclude_list = [".git", "__pycache__", ".DS_Store", "__init__.py", "LOG", "legacy", "tests"]

    if os.path.exists(project_path):
        print(project_path)
        print_tree(project_path, exclude_files=exclude_list)
    else:
        print("Указанный путь не существует.")

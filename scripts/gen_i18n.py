import json
import re
from pathlib import Path

def to_pascal(snake_str: str) -> str:
    return "".join(p.capitalize() for p in snake_str.split('_') if p)

def generate_classes(name: str, data: dict, path_parts: list | None = None) -> list:
    if path_parts is None:
        path_parts = []
        
    functor_lines = []
    class_lines = [f"class {name}:"]
    
    if not path_parts:
        class_lines.extend([
            '    """',
            '    [Root Object] I18n Keys Mapping',
            '    ',
            '    Provides strongly-typed, auto-completed access to all translation keys.',
            '    - Navigate nested keys using dot notation.',
            '    - If a key requires formatting (e.g., {item}), call it as a function.',
            '    """'
        ])
    else:
        current_node = to_pascal(path_parts[-1])
        class_lines.extend([
            '    """',
            f'    [Key Type] {current_node}',
            '    """'
        ])
        
    for key, value in data.items():
        full_path = ".".join(path_parts + [key])
        safe_key = f"_{key}" if key[0].isdigit() else key
        pascal_key = to_pascal(key)
        prefix = "".join(to_pascal(p) for p in path_parts)
        
        if isinstance(value, dict):
            sub_class_name = f"_{prefix}{pascal_key}K"
            child_lines = generate_classes(sub_class_name, value, path_parts + [key])
            functor_lines = child_lines + functor_lines
            
            class_lines.append(f"    {safe_key}: {sub_class_name} = {sub_class_name}()")
            class_lines.append(f'    """[Key Type] {pascal_key}"""')
            
        else:
            vars_in_string = re.findall(r'\{(\w+)\}', str(value))
            
            if not vars_in_string:
                class_lines.append(f'    {safe_key}: str = "{full_path}"')
                class_lines.append(f'    """[Props Type] {pascal_key}"""')
            else:
                unique_vars = list(dict.fromkeys(vars_in_string))

                def param_type(name: str) -> str:
                    if name == "error":
                        return "Exception | str | int"
                    if name == "path":
                        return "str | int | Path"
                    return "str | int"

                args_str = ", ".join(f"{v}: {param_type(v)}" for v in unique_vars)
                dict_str = ", ".join(f'"{v}": {v}' for v in unique_vars)
                
                safe_class_name_part = f"_{pascal_key}" if pascal_key[0].isdigit() else pascal_key
                functor_name = f"_{prefix}{safe_class_name_part}Callable"
                
                functor_lines.extend([
                    f"class {functor_name}:",
                    f'    """',
                    f'    [Callable Props Type] {pascal_key}',
                    f'    ',
                    f'    Original template: "{value}"',
                    f'    """',
                    f"    def __call__(self, *, {args_str}) -> tuple[str, dict]:",
                    f'        """',
                    f'        Formats the translation string.',
                    f'        ',
                    f'        Args:'
                ])
                
                for var in unique_vars:
                    functor_lines.append(f'            {var} ({param_type(var)}): Dynamic value for {{{var}}}.')
                
                functor_lines.extend([
                    f'        ',
                    f'        Returns:',
                    f'            tuple[str, dict]: Key path and formatting dictionary.',
                    f'        """',
                    f'        return ("{full_path}", {{{dict_str}}})',
                    ""
                ])
                
                class_lines.append(f"    {safe_key}: {functor_name} = {functor_name}()")
                class_lines.extend([
                    f'    """',
                    f'    [Callable Props Type] {pascal_key}',
                    f'    ',
                    f'    Original template: "{value}"',
                    f'    """'
                ])
                
    return functor_lines + class_lines + [""]

def run_generator():
    locales_path = Path("tetodl/locales/en.json")
    output_path = Path("tetodl/utils/i18n_keys.py")
    
    with open(locales_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    final_lines = generate_classes("I18nKeysMap", data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""AUTO-GENERATED FILE. DO NOT EDIT."""\n')
        f.write('from pathlib import Path\n')
        f.write('from typing import TypeAlias, Tuple, Dict, Any, Union\n\n')
        f.write('I18nKey: TypeAlias = Union[str, Tuple[str, Dict[str, Any]]]\n\n')
        
        f.write("\n".join(final_lines))

        f.write("\nKeys = I18nKeysMap()\n")
        f.write('"""\n')
        f.write('[Root Object] I18n Keys Mapping\n\n')
        f.write('Provides strongly-typed, auto-completed access to all translation keys.\n')
        f.write('- Navigate nested keys using dot notation.\n')
        f.write('- If a key requires formatting (e.g., {item}), call it as a function.\n')
        f.write('"""\n')

if __name__ == "__main__":
    run_generator()
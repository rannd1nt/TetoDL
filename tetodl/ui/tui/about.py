import time

import questionary
from questionary import Choice, Separator
from rich.padding import Padding
from rich.text import Text

from ...constants import APP_VERSION
from ...utils.display import visit_github, visit_instagram
from ...utils.console import console
from ...utils.formatters import clear, menu_style
from ...utils.i18n import get_text as _
from ...utils.i18n_keys import Keys


def menu_about():
    """About menu"""
    while True:
        clear()
        console.rich.print()

        title_text = f"> {_(Keys.menu.about.title(version=APP_VERSION))} <"
        console.rich.print(Padding(title_text, pad=(0, 3)), style="bold bright_cyan")

        subtitle_text = _(Keys.menu.about.subtitle)
        console.rich.print(Padding(subtitle_text, (0, 3)), style="bold bright_red")

        description = _(Keys.menu.about.description)
        console.rich.print()

        max_len = 65
        current_term_width = console.rich.width - 3
        final_width = min(max_len, current_term_width)

        console.rich.print(
            Padding(description, (0, 3)), 
            width=final_width, 
            style="white",
            justify="left" 
        )
        console.rich.print()


        info_content = Text()
        
        info_content.append("Author : ", style="bold bright_cyan")
        info_content.append("Zahraaan Dzakii / rannd1nt\n", style="white")
        
        info_content.append("Email  : ", style="bold bright_cyan")
        info_content.append("zahraandzakiits@gmail.com", style="white")
        info_content.append("\n\n")
        info_content.append("Copyright (c) 2026 rannd1nt. All rights reserved.", style="white")

        console.rich.print(Padding(info_content, (0, 3)))

        choices = [
            Separator(line="-"*25),
            Choice(title=f"- {_(Keys.menu.about.documentation)}", value="doc"),
            Choice(title=f"- {_(Keys.menu.about.github)}", value="github"),
            Choice(title=f"- {_(Keys.menu.about.instagram)}", value="instagram"),
            Separator(line="-"*25),
            Choice(title=f"- {_(Keys.common.back)}", value="back"),
        ]

        selection = questionary.select(
            message="",
            choices=choices,
            style=menu_style(),
            qmark="",
            pointer=">",
            use_indicator=False,
            instruction=" "
        ).ask()

        if selection is None or selection == "back":
            break

        if selection == "doc":
            clear()
            msg = Padding(f"[!] {_(Keys.error.documentation_unavailable)}", pad=(25))
            console.rich.print(msg, style="bold yellow", justify='center')
            time.sleep(1.5)
            
        elif selection == "github":
            visit_github()
            
        elif selection == "instagram":
            visit_instagram()
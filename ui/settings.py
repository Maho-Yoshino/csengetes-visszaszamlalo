if __name__ == "__main__":
    from sys import path as sp
    from os import path
    sp.append(path.abspath(path.join(path.dirname(__file__), '..')))

from ctypes import windll
from datetime import date, datetime, timedelta
from logging import getLogger
from pathlib import Path
from tkinter import (
    BooleanVar,
    Canvas,
    Checkbutton,
    END,
    Frame,
    Listbox,
    Menu,
    StringVar,
    Text,
    Toplevel,
    colorchooser,
    messagebox,
)
from tkinter import ttk

import modules.state as state

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NONE_TOKEN = "<none>"


class settingsGUI(Toplevel):
    content: Frame

    def __init__(self):
        self.logger = getLogger(__name__)
        if state.openGUIs.get("settings") is not None:
            state.openGUIs["settings"]._focus_window()
            return self.logger.debug("Settings opened more than once. Focus set to older window")

        super().__init__(state.clock)
        state.openGUIs["settings"] = self
        self.protocol("WM_DELETE_WINDOW", self._closeFunc)

        self.bg = "#202020"
        self.fg = "#FFFFFF"
        self.surface = "#2B2B2B"
        self.accent = "#3A3A3A"
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("TFrame", background=self.bg)
        self.style.configure("TLabel", foreground=self.fg, background=self.bg)
        self.style.configure("mainText.Label", foreground=self.fg, background=self.bg)
        self.style.configure("TButton", foreground=self.fg, background=self.surface)
        self.style.map("TButton", background=[("active", self.accent)])
        self.style.configure("scheduleElement.TButton", padding=8, foreground=self.fg, background=self.surface)
        self.style.map("scheduleElement.TButton", background=[("active", self.accent)])
        self.style.configure("TLabelframe", background=self.bg, foreground=self.fg)
        self.style.configure("TLabelframe.Label", background=self.bg, foreground=self.fg)
        self.style.configure("TEntry", fieldbackground=self.surface, foreground=self.fg, insertcolor=self.fg)
        self.style.configure("TCombobox", fieldbackground=self.surface, foreground=self.fg, background=self.surface, arrowcolor=self.fg)
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.surface)],
            foreground=[("readonly", self.fg)],
            selectbackground=[("readonly", self.accent)],
            selectforeground=[("readonly", self.fg)],
        )
        self.style.configure("TSpinbox", fieldbackground=self.surface, foreground=self.fg, background=self.surface, arrowcolor=self.fg)
        self.style.configure("TCheckbutton", background=self.bg, foreground=self.fg)
        self.style.configure("TNotebook", background=self.bg)
        self.style.configure("TNotebook.Tab", foreground=self.fg, background=self.surface)
        self.configure(background=self.bg)

        loc = state.settings.localization
        self.title(loc.settings.title)
        self.state("zoomed")

        menu = Menu(self, background=self.bg, fg=self.fg, relief="ridge", activebackground=self.accent, activeforeground=self.fg)
        menu.add_command(label=loc.settings.topbar["schedule"], command=self._openSchedule)
        menu.add_command(label=loc.settings.topbar["general"], command=self._openGeneral)
        self.config(menu=menu)

        self.content = Frame(self, bg=self.bg)
        self.content.pack(fill="both", expand=True, padx=12, pady=12)
        self._openSchedule()
        self.after(0, self._focus_window)

    def _closeFunc(self):
        state.openGUIs.pop("settings", None)
        self.destroy()

    def _refresh_clock_runtime(self):
        state.settings.reload()
        state.clock.refreshFromSettings()

    def _focus_window(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(100, lambda: self.attributes("-topmost", False))
            windll.user32.ShowWindow(self.winfo_id(), 9)
            windll.user32.SetForegroundWindow(self.winfo_id())
        except Exception:
            self.logger.exception("Could not force settings window focus")

    def _close_child_window(self, dialog: Toplevel):
        dialog.destroy()
        self.after(0, self._focus_window)

    def _clearContent(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _current_week_start(self) -> date:
        today = state.getTime().date()
        return today - timedelta(days=today.weekday())

    def _style_tk_frame(self, widget: Frame):
        widget.configure(bg=self.bg)

    def _style_listbox(self, widget: Listbox):
        widget.configure(
            bg=self.surface,
            fg=self.fg,
            selectbackground=self.accent,
            selectforeground=self.fg,
            highlightbackground=self.bg,
            highlightcolor=self.accent,
        )

    def _style_text(self, widget: Text):
        widget.configure(
            bg=self.surface,
            fg=self.fg,
            insertbackground=self.fg,
            highlightbackground=self.bg,
            highlightcolor=self.accent,
        )

    def _style_checkbutton(self, widget: Checkbutton):
        widget.configure(
            bg=self.bg,
            fg=self.fg,
            activebackground=self.bg,
            activeforeground=self.fg,
            selectcolor=self.surface,
        )

    def _style_dialog(self, widget: Toplevel):
        widget.configure(bg=self.bg)

    def _format_class_value(self, value) -> str:
        classes = state.settings.classes.classes
        if value is None:
            return NONE_TOKEN
        if isinstance(value, list):
            formatted = []
            for item in value:
                if item is None:
                    formatted.append(NONE_TOKEN)
                elif isinstance(item, str):
                    formatted.append(item)
                elif isinstance(item, dict):
                    formatted.append(item.get("name", "custom"))
            return ", ".join(formatted)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            name = value.get("name", "custom")
            teacher = value.get("teacher")
            return f"{name} ({teacher})" if teacher else name
        return str(value)

    def _class_option_label(self, code: str, data: dict[str, str]) -> str:
        return f"{data.get('teacher', '')}: {data.get('name', code)} ({data.get('room', '')})"

    def _class_option_lookup(self) -> dict[str, str | None]:
        return {"Null": None} | {
            self._class_option_label(code, data): code
            for code, data in sorted(state.settings.classes.classes.items(), key=lambda item: self._class_option_label(item[0], item[1]).lower())
        }

    def _class_label_for_value(self, value, class_options: dict[str, str | None]) -> str:
        if value is None:
            return "Null"
        if isinstance(value, str) and value in state.settings.classes.classes:
            label = self._class_option_label(value, state.settings.classes.classes[value])
            if label in class_options:
                return label
        return "Null"

    def _group_values_for_slot(self, value) -> list[object]:
        if isinstance(value, list):
            return value or [None]
        if value is None:
            return [None]
        return [value]

    def _visible_group_count(self, values: list[object]) -> int:
        return max(1, sum(1 for value in values if value is not None))

    def _schedule_class_width(self, entries_by_day: dict[int, dict[int, object]]) -> int:
        longest = len("Wed")
        for day_entries in entries_by_day.values():
            for entry in day_entries.values():
                for value in entry.data or [None]:
                    if value is None:
                        continue
                    class_data = self._class_display_data(value)
                    longest = max(
                        longest,
                        len(class_data["name"]),
                        len(class_data["teacher"]),
                        len(class_data["room"]),
                    )
        return min(max(longest * 3 + 10, 48), 84)

    def _class_display_data(self, value) -> dict[str, str]:
        if all(hasattr(value, attr) for attr in ("name", "teacher", "room")):
            return {
                "name": value.name or "",
                "teacher": value.teacher or "",
                "room": value.room or "",
            }
        if isinstance(value, str):
            data = state.settings.classes.classes.get(value, {})
            return {
                "name": data.get("name", value),
                "teacher": data.get("teacher", ""),
                "room": data.get("room", ""),
            }
        if isinstance(value, dict):
            return {
                "name": value.get("name", ""),
                "teacher": value.get("teacher", ""),
                "room": value.get("room", ""),
            }
        if isinstance(value, list):
            items = [self._class_display_data(item) for item in value if item is not None]
            return {
                "name": " / ".join(item["name"] for item in items if item["name"]),
                "teacher": " / ".join(item["teacher"] for item in items if item["teacher"]),
                "room": " / ".join(item["room"] for item in items if item["room"]),
            }
        return {"name": NONE_TOKEN, "teacher": "", "room": ""}

    def _teacher_display_value(self, value) -> str:
        return self._class_display_data(value)["teacher"].strip()

    def _substituted_groups(self, day_index: int, slot: int, week_start: date, value_count: int) -> list[bool]:
        key = (week_start + timedelta(days=day_index)).strftime("%Y-%m-%d")
        special_day = state.settings.events._data["specialDays"].get(key, {})
        classes = special_day.get("classes", {}) if isinstance(special_day, dict) else {}
        slot_key = str(slot)
        if slot_key not in classes:
            return [False] * value_count

        special_values = self._group_values_for_slot(classes[slot_key])
        usual_values = self._group_values_for_slot(self._raw_weekly_value(day_index, slot))
        substitutions = []
        for index in range(value_count):
            special_value = special_values[index] if index < len(special_values) else None
            usual_value = usual_values[index] if index < len(usual_values) else None
            special_teacher = self._teacher_display_value(special_value)
            usual_teacher = self._teacher_display_value(usual_value)
            substitutions.append(bool(special_teacher) and special_teacher != usual_teacher)
        return substitutions

    def _event_items(self, kind: str, date_key: str, slot: int) -> list[dict[str, object]]:
        return [
            item
            for item in state.settings.events._data[kind].get(date_key, [])
            if item.get("class") == slot
        ]

    def _class_alert_items(self, date_key: str, slot: int) -> list[tuple[int, dict[str, object]]]:
        return [
            (index, item)
            for index, item in enumerate(state.settings.events._data["alerts"])
            if item.get("classDate", item.get("date")) == date_key and item.get("class") == slot
        ]

    def _format_class_alert(self, alert: dict[str, object]) -> str:
        relative_to = "end" if alert.get("relativeTo") == "end" else "start"
        minutes = alert.get("minutes", 0)
        message = alert.get("message", "")
        base = "before end" if relative_to == "end" else "since start"
        keep = "keep" if alert.get("keep", False) else "once"
        return f"{alert.get('time', '--:--')} | {minutes} min {base} | {keep} | {message}"

    def _redraw_class_box(self, canvas: Canvas, lines: list[str], substituted: bool):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 56)
        height = max(canvas.winfo_height(), 46)
        canvas.create_rectangle(1, 1, width - 2, height - 2, fill=self.surface, outline=self.accent)
        y = 8
        for line in lines:
            canvas.create_text(5, y, text=line or "-", anchor="w", fill=self.fg, font=state.fontSize(7), width=max(width - 10, 46))
            y += 14
        if substituted:
            canvas.create_line(5, height - 5, width - 5, height - 5, fill="#89470C", width=2, capstyle="round")

    def _create_class_box(self, parent, *, lines: list[str], substituted: bool, command):
        canvas = Canvas(parent, bg=self.bg, highlightthickness=0, width=56, height=50, cursor="hand2")
        canvas.bind("<Configure>", lambda _event: self._redraw_class_box(canvas, lines, substituted))
        canvas.bind("<Button-1>", lambda _event: command())
        return canvas

    def _create_grouped_class_cell(self, parent, *, values: list[object], substitutions: list[bool], command):
        cell = ttk.Frame(parent)
        cell.bind("<Button-1>", lambda _event: command())
        values = values or [None]
        is_split = len(values) > 1
        for index, value in enumerate(values, start=1):
            if is_split and value is None:
                continue
            group = ttk.Frame(cell)
            group.pack(side="left", fill="both", expand=True, padx=(0 if index == 1 else 2, 0))
            if is_split:
                ttk.Label(group, text=f"Group {index}", anchor="w").pack(fill="x")
            class_data = self._class_display_data(value)
            box = self._create_class_box(
                group,
                lines=[class_data["name"], class_data["teacher"], class_data["room"]],
                substituted=substitutions[index - 1] if index - 1 < len(substitutions) else False,
                command=command,
            )
            box.pack(fill="both", expand=True)
        return cell

    def _create_empty_slot_area(self, parent, *, day_index: int, slot: int):
        frame = Frame(parent, bg=self.bg, cursor="hand2")
        frame.bind("<Double-Button-1>", lambda _event: self._open_assignment_prompt(day_index, slot))
        return frame

    def _slot_time_string(self, slot: int) -> str:
        return state.settings.schedule._data["timeSlots"].get(str(slot), "00:00-00:00")

    def _open_assignment_prompt(self, day_index: int, slot: int, *, add_group: bool = False):
        class_options = self._class_option_lookup()
        option_labels = list(class_options.keys())
        if not option_labels:
            return messagebox.showerror("No classes", "Add classes to config/classes.json before assigning schedule slots.", parent=self)

        dialog = Toplevel(self)
        self._style_dialog(dialog)
        dialog.title(f"Add class to {DAY_NAMES[day_index]}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_child_window(dialog))

        current_value = self._raw_weekly_value(day_index, slot)
        group_values = self._group_values_for_slot(current_value)
        if add_group:
            group_values.append(None)
        class_vars: list[StringVar] = []
        secondary_var = BooleanVar(value=str(slot) in state.settings.schedule._data["secondary"].get(str(day_index), {}))
        one_day_var = BooleanVar(value=False)

        ttk.Label(dialog, text="Class number").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        ttk.Label(dialog, text=str(slot), style="mainText.Label").grid(row=0, column=1, sticky="w", padx=10, pady=(10, 4))

        class_rows = ttk.Frame(dialog)
        class_rows.grid(row=1, column=0, columnspan=2, sticky="ew")
        class_rows.grid_columnconfigure(1, weight=1)
        dropdown_width = max(len(label) for label in option_labels) + 2

        def redraw_class_rows():
            for child in class_rows.winfo_children():
                child.destroy()
            for index, var in enumerate(class_vars, start=1):
                ttk.Label(class_rows, text=f"Class ({index})").grid(row=index - 1, column=0, sticky="w", padx=10, pady=4)
                ttk.Combobox(
                    class_rows,
                    textvariable=var,
                    values=option_labels,
                    state="readonly",
                    width=dropdown_width,
                ).grid(row=index - 1, column=1, sticky="ew", padx=10, pady=4)

        for value in group_values:
            class_vars.append(StringVar(value=self._class_label_for_value(value, class_options)))
        redraw_class_rows()

        secondary_check = Checkbutton(dialog, text="Set only for secondary week", variable=secondary_var)
        self._style_checkbutton(secondary_check)
        secondary_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=4)

        def toggle_one_day():
            if one_day_var.get():
                secondary_var.set(False)
                secondary_check.configure(state="disabled")
            else:
                secondary_check.configure(state="normal")

        one_day_check = Checkbutton(dialog, text="Set only for this day", variable=one_day_var, command=toggle_one_day)
        self._style_checkbutton(one_day_check)
        one_day_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=4)
        dialog.grid_columnconfigure(1, weight=1)

        def save_assignment():
            selected_groups = [class_options[var.get()] for var in class_vars]
            class_code = selected_groups[0] if len(selected_groups) == 1 else selected_groups
            if one_day_var.get():
                date_key = (self._current_week_start() + timedelta(days=day_index)).strftime("%Y-%m-%d")
                special_day = state.settings.events._data["specialDays"].setdefault(date_key, {"full": False})
                special_day.setdefault("full", False)
                special_day.setdefault("classes", {})[str(slot)] = class_code
                special_day.setdefault("timeSlots", {})[str(slot)] = self._slot_time_string(slot)
                state.settings.events.save()
            else:
                state.settings.schedule._data["timeSlots"].setdefault(str(slot), self._slot_time_string(slot))
                while len(state.settings.schedule._data["default"]) <= day_index:
                    state.settings.schedule._data["default"].append({})
                if secondary_var.get():
                    state.settings.schedule._data["secondary"].setdefault(str(day_index), {})[str(slot)] = class_code
                else:
                    state.settings.schedule._data["default"][day_index][str(slot)] = class_code
                    state.settings.schedule._data["secondary"].get(str(day_index), {}).pop(str(slot), None)
                state.settings.schedule.save()
            self._openSchedule()
            self._close_child_window(dialog)

        buttons = ttk.Frame(dialog)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        ttk.Button(buttons, text="Save", command=save_assignment).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=lambda: self._close_child_window(dialog)).pack(side="left", padx=(6, 0))

        def split_class():
            class_vars.append(StringVar(value="Null"))
            redraw_class_rows()
            dialog.update_idletasks()
            dialog.geometry(f"{dialog.winfo_reqwidth()}x{dialog.winfo_reqheight()}")

        def remove_split():
            if len(class_vars) > 1:
                class_vars.pop()
                redraw_class_rows()
                dialog.update_idletasks()
                dialog.geometry(f"{dialog.winfo_reqwidth()}x{dialog.winfo_reqheight()}")

        ttk.Button(buttons, text="Split class", command=split_class).pack(side="left", padx=(6, 0))
        ttk.Button(buttons, text="Remove split", command=remove_split).pack(side="left", padx=(6, 0))
        dialog.update_idletasks()
        dialog.geometry(f"{dialog.winfo_reqwidth()}x{dialog.winfo_reqheight()}")
        self._refresh_clock_runtime()

    def _parse_class_entry(self, raw: str):
        text = raw.strip()
        if not text:
            return None
        parts = [part.strip() for part in text.split(",")]
        parsed = []
        for part in parts:
            if not part:
                continue
            if part.lower() == NONE_TOKEN.lower():
                parsed.append(None)
                continue
            if part not in state.settings.classes.classes:
                raise ValueError(f"Unknown class code: {part}")
            parsed.append(part)
        if not parsed:
            return None
        if len(parsed) == 1:
            return parsed[0]
        return parsed

    def _parse_timestring(self, value: str) -> str:
        text = value.strip()
        datetime.strptime(text, "%H:%M")
        return text

    def _available_languages(self) -> list[str]:
        return sorted(path.stem for path in Path("lang").glob("*.json"))

    def _create_time_inputs(self, parent, *, start: str = ""):
        hour_var = StringVar(value="00")
        minute_var = StringVar(value="00")
        if start:
            parsed = datetime.strptime(start, "%H:%M")
            hour_var.set(f"{parsed.hour:02}")
            minute_var.set(f"{parsed.minute:02}")
        frame = ttk.Frame(parent)
        ttk.Spinbox(frame, from_=0, to=23, width=3, format="%02.0f", textvariable=hour_var, wrap=True).pack(side="left")
        ttk.Label(frame, text=":").pack(side="left")
        ttk.Spinbox(frame, from_=0, to=59, width=3, format="%02.0f", textvariable=minute_var, wrap=True).pack(side="left")
        return frame, hour_var, minute_var

    def _time_from_vars(self, hour_var: StringVar, minute_var: StringVar) -> str:
        hour = int(hour_var.get())
        minute = int(minute_var.get())
        if hour not in range(24) or minute not in range(60):
            raise ValueError("Invalid time value.")
        return f"{hour:02}:{minute:02}"

    def _create_date_inputs(self, parent, *, value: str | None = None):
        today = state.getTime().date()
        parsed = today
        if value:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
        year_var = StringVar(value=str(parsed.year))
        month_var = StringVar(value=f"{parsed.month:02}")
        day_var = StringVar(value=f"{parsed.day:02}")
        frame = ttk.Frame(parent)
        ttk.Spinbox(frame, from_=today.year - 10, to=today.year + 10, width=5, textvariable=year_var, wrap=True).pack(side="left")
        ttk.Label(frame, text="-").pack(side="left")
        ttk.Spinbox(frame, from_=1, to=12, width=3, format="%02.0f", textvariable=month_var, wrap=True).pack(side="left")
        ttk.Label(frame, text="-").pack(side="left")
        ttk.Spinbox(frame, from_=1, to=31, width=3, format="%02.0f", textvariable=day_var, wrap=True).pack(side="left")
        return frame, year_var, month_var, day_var

    def _date_from_vars(self, year_var: StringVar, month_var: StringVar, day_var: StringVar) -> str:
        value = date(int(year_var.get()), int(month_var.get()), int(day_var.get()))
        return value.strftime("%Y-%m-%d")

    def _openSchedule(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        week_start = self._current_week_start()
        ttk.Label(root, text=f"Week {week_start.isocalendar().week}", style="mainText.Label", anchor="center", justify="center").pack(fill="x")
        instruction_label = ttk.Label(
            root,
            text="Click a class slot to edit the weekly schedule for that day. Use comma-separated class codes for grouped classes.",
            style="mainText.Label",
            anchor="center",
            justify="center",
        )
        instruction_label.pack(fill="x", pady=(0, 12))
        root.bind("<Configure>", lambda event: instruction_label.configure(wraplength=max(event.width - 24, 120)))

        unified = state.settings.schedule.getUnifiedSchedule(week_of=state.getTime())
        entries_by_day = {
            day_index: {entry.classIndex: entry for entry in sorted(unified[day_index], key=lambda item: item.classIndex)}
            if day_index < len(unified)
            else {}
            for day_index in range(7)
        }
        slot_indexes = sorted({slot for day_entries in entries_by_day.values() for slot in day_entries})
        max_groups_by_slot = {
            slot: max(self._visible_group_count(day_entries[slot].data or [None]) for day_entries in entries_by_day.values() if slot in day_entries)
            for slot in slot_indexes
        }
        max_groups_by_day = {
            day_index: max((self._visible_group_count(entry.data or [None]) for entry in day_entries.values()), default=1)
            for day_index, day_entries in entries_by_day.items()
        }
        class_box_width = self._schedule_class_width(entries_by_day)

        schedule_outer = ttk.Frame(root)
        schedule_outer.pack(fill="both", expand=True, pady=(0, 18))
        schedule_canvas = Canvas(schedule_outer, bg=self.bg, highlightthickness=0, height=300)
        schedule_vscroll = ttk.Scrollbar(schedule_outer, orient="vertical", command=schedule_canvas.yview)
        schedule_hscroll = ttk.Scrollbar(schedule_outer, orient="horizontal", command=schedule_canvas.xview)
        schedule_canvas.configure(yscrollcommand=schedule_vscroll.set, xscrollcommand=schedule_hscroll.set)
        schedule_canvas.grid(row=0, column=0, sticky="nsew")
        schedule_vscroll.grid(row=0, column=1, sticky="ns")
        schedule_hscroll.grid(row=1, column=0, sticky="ew")
        schedule_outer.grid_columnconfigure(0, weight=1)
        schedule_outer.grid_rowconfigure(0, weight=1)

        schedule_grid = ttk.Frame(schedule_canvas)
        schedule_window = schedule_canvas.create_window((0, 0), window=schedule_grid, anchor="nw")

        def update_schedule_scrollregion(_event=None):
            schedule_canvas.configure(scrollregion=schedule_canvas.bbox("all"))
            bbox = schedule_canvas.bbox("all")
            if bbox and bbox[2] > schedule_canvas.winfo_width():
                schedule_hscroll.grid()
            else:
                schedule_hscroll.grid_remove()

        def resize_schedule_grid(event):
            schedule_canvas.itemconfigure(schedule_window, width=max(event.width, schedule_grid.winfo_reqwidth()))

        def bind_schedule_wheel(_event=None):
            schedule_canvas.bind_all("<MouseWheel>", on_schedule_wheel)
            schedule_canvas.bind_all("<Shift-MouseWheel>", on_schedule_shift_wheel)

        def unbind_schedule_wheel(_event=None):
            schedule_canvas.unbind_all("<MouseWheel>")
            schedule_canvas.unbind_all("<Shift-MouseWheel>")

        def on_schedule_wheel(event):
            schedule_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_schedule_shift_wheel(event):
            schedule_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        schedule_grid.bind("<Configure>", update_schedule_scrollregion)
        schedule_canvas.bind("<Configure>", resize_schedule_grid)
        schedule_canvas.bind("<Enter>", bind_schedule_wheel)
        schedule_canvas.bind("<Leave>", unbind_schedule_wheel)
        schedule_grid.bind("<Enter>", bind_schedule_wheel)
        schedule_grid.bind("<Leave>", unbind_schedule_wheel)

        for day_index in range(7):
            schedule_grid.grid_columnconfigure(day_index, weight=1, minsize=class_box_width * max_groups_by_day[day_index])
            header = (week_start + timedelta(days=day_index)).strftime("%a\n%Y-%m-%d")
            header_label = ttk.Label(schedule_grid, text=header, anchor="center", justify="center", wraplength=max(class_box_width * max_groups_by_day[day_index], 48))
            header_label.grid(
                row=0,
                column=day_index,
                sticky="nsew",
                padx=2,
                pady=(0, 2),
            )

        for row_index, slot_index in enumerate(slot_indexes, start=1):
            schedule_grid.grid_rowconfigure(row_index, weight=1, uniform="schedule_slots", minsize=72 if max_groups_by_slot[slot_index] > 1 else 56)
            for day_index in range(7):
                entry = entries_by_day[day_index].get(slot_index)
                if entry is None:
                    self._create_empty_slot_area(schedule_grid, day_index=day_index, slot=slot_index).grid(
                        row=row_index,
                        column=day_index,
                        sticky="nsew",
                        padx=2,
                        pady=2,
                    )
                else:
                    values = entry.data or [None]
                    class_box = self._create_grouped_class_cell(
                        schedule_grid,
                        values=values,
                        substitutions=self._substituted_groups(day_index, entry.classIndex, week_start, len(values)),
                        command=lambda d=day_index, s=entry.classIndex, e=entry: self._open_class_slot(d, s, e),
                    )
                    class_box.grid(row=row_index, column=day_index, sticky="nsew", padx=2, pady=2)

        add_row = len(slot_indexes) + 1
        schedule_grid.grid_rowconfigure(add_row, weight=1, uniform="schedule_slots", minsize=36)
        for day_index in range(7):
            next_slot = max(entries_by_day[day_index], default=0) + 1
            ttk.Button(schedule_grid, text="Add slot", command=lambda d=day_index, s=next_slot: self._open_assignment_prompt(d, s)).grid(
                row=add_row,
                column=day_index,
                sticky="nsew",
                padx=2,
                pady=2,
            )

    def _raw_weekly_value(self, day_index: int, slot: int):
        schedule_data = state.settings.schedule._data
        is_secondary = state.settings.schedule.currentlySecondaryWeek(state.getTime())
        if is_secondary:
            slot_value = schedule_data["secondary"].get(str(day_index), {}).get(str(slot), None)
            if slot_value is not None or str(slot) in schedule_data["secondary"].get(str(day_index), {}):
                return slot_value
        if day_index >= len(schedule_data["default"]):
            return None
        return schedule_data["default"][day_index].get(str(slot))

    def _open_class_slot(self, day_index: int, slot: int, entry):
        dialog = Toplevel(self)
        self._style_dialog(dialog)
        dialog.title(f"{DAY_NAMES[day_index]} class")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("460x380")
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_child_window(dialog))

        week_start = self._current_week_start()
        class_date = week_start + timedelta(days=day_index)
        date_key = class_date.strftime("%Y-%m-%d")
        class_data = self._class_display_data(entry.data)

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        class_tab = ttk.Frame(notebook)
        events_tab = ttk.Frame(notebook)
        alerts_tab = ttk.Frame(notebook)
        notebook.add(class_tab, text="Class data")
        notebook.add(events_tab, text="Events")
        notebook.add(alerts_tab, text="Alerts")

        rows = [
            ("Date", date_key),
            ("Time", f"{entry.start.strftime('%H:%M')}-{entry.end.strftime('%H:%M')}"),
            ("Class name", class_data["name"]),
            ("Teacher name", class_data["teacher"]),
            ("Room", class_data["room"]),
            ("Class number in the day", str(slot)),
        ]
        for row, (label, value) in enumerate(rows):
            ttk.Label(class_tab, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=5)
            ttk.Label(class_tab, text=value or "-", style="mainText.Label").grid(row=row, column=1, sticky="w", padx=8, pady=5)
        class_tab.grid_columnconfigure(1, weight=1)

        class_buttons = ttk.Frame(class_tab)
        class_buttons.grid(row=len(rows), column=0, columnspan=2, sticky="w", padx=8, pady=(12, 0))
        ttk.Button(class_buttons, text="Change class", command=lambda: (dialog.destroy(), self._open_assignment_prompt(day_index, slot))).pack(side="left")
        ttk.Button(class_buttons, text="Add group", command=lambda: (dialog.destroy(), self._open_assignment_prompt(day_index, slot, add_group=True))).pack(side="left", padx=(6, 0))
        ttk.Button(class_buttons, text="Delete slot", command=lambda: self._delete_weekly_slot(day_index, slot, dialog)).pack(side="left", padx=(6, 0))

        event_type_var = StringVar(value="Homework")
        event_topic = Text(events_tab, height=4, width=36)
        self._style_text(event_topic)
        homework_list = Listbox(events_tab, exportselection=False, height=4)
        exam_list = Listbox(events_tab, exportselection=False, height=4)
        self._style_listbox(homework_list)
        self._style_listbox(exam_list)

        def refresh_events():
            homework_list.delete(0, END)
            exam_list.delete(0, END)
            for item in self._event_items("homework", date_key, slot):
                homework_list.insert(END, item.get("topic", ""))
            for item in self._event_items("exams", date_key, slot):
                exam_list.insert(END, item.get("topic", ""))

        ttk.Label(events_tab, text="Homework").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        homework_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        ttk.Label(events_tab, text="Exam").grid(row=2, column=0, sticky="w", padx=8, pady=(8, 2))
        exam_list.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))

        event_form = ttk.Frame(events_tab)
        event_form.grid(row=4, column=0, sticky="ew", padx=8, pady=8)
        ttk.Combobox(event_form, textvariable=event_type_var, values=["Homework", "Exam"], state="readonly", width=14).grid(row=0, column=0, sticky="w", pady=(0, 4))
        event_topic.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))
        events_tab.grid_columnconfigure(0, weight=1)
        events_tab.grid_rowconfigure(1, weight=1)
        events_tab.grid_rowconfigure(3, weight=1)

        def add_event():
            topic = event_topic.get("1.0", END).strip()
            if not topic:
                return messagebox.showerror("Invalid event", "Event text is required.", parent=dialog)
            key = "homework" if event_type_var.get() == "Homework" else "exams"
            state.settings.events._data[key].setdefault(date_key, []).append({"class": slot, "topic": topic})
            state.settings.events.save()
            event_topic.delete("1.0", END)
            refresh_events()
            self._refresh_clock_runtime()

        def remove_event():
            if homework_list.curselection():
                key = "homework"
                listbox = homework_list
            elif exam_list.curselection():
                key = "exams"
                listbox = exam_list
            else:
                return
            if not listbox.curselection():
                return
            selected_index = listbox.curselection()[0]
            seen = -1
            kept = []
            for item in state.settings.events._data[key].get(date_key, []):
                if item.get("class") == slot:
                    seen += 1
                    if seen == selected_index:
                        continue
                kept.append(item)
            if kept:
                state.settings.events._data[key][date_key] = kept
            else:
                state.settings.events._data[key].pop(date_key, None)
            state.settings.events.save()
            refresh_events()
            self._refresh_clock_runtime()

        event_buttons = ttk.Frame(events_tab)
        event_buttons.grid(row=6, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(event_buttons, text="Add", command=add_event).pack(side="left")
        ttk.Button(event_buttons, text="Remove", command=remove_event).pack(side="left", padx=(6, 0))
        refresh_events()

        ttk.Label(
            alerts_tab,
            text="Alert time is calculated relative to the beginning or end of this class.",
            style="mainText.Label",
            wraplength=400,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 6))
        alert_list = Listbox(alerts_tab, exportselection=False, height=8)
        self._style_listbox(alert_list)
        alert_list.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(8, 6), pady=(0, 8))
        alerts_tab.grid_columnconfigure(0, weight=1)
        alerts_tab.grid_rowconfigure(1, weight=1)
        current_alert_indexes: list[int] = []

        def refresh_alerts():
            current_alert_indexes.clear()
            alert_list.delete(0, END)
            for alert_index, alert in self._class_alert_items(date_key, slot):
                current_alert_indexes.append(alert_index)
                alert_list.insert(END, self._format_class_alert(alert))

        def remove_alert():
            if not alert_list.curselection():
                return
            alert_index = current_alert_indexes[alert_list.curselection()[0]]
            state.settings.events._data["alerts"].pop(alert_index)
            state.settings.events.save()
            refresh_alerts()
            self._refresh_clock_runtime()

        def open_alert_prompt(alert_index: int | None = None):
            existing_alert = state.settings.events._data["alerts"][alert_index] if alert_index is not None else {}
            alert_dialog = Toplevel(dialog)
            self._style_dialog(alert_dialog)
            alert_dialog.title("Edit alert" if alert_index is not None else "Add alert")
            alert_dialog.transient(dialog)
            alert_dialog.grab_set()

            def close_alert_dialog():
                alert_dialog.destroy()
                dialog.lift()
                dialog.focus_force()

            alert_dialog.protocol("WM_DELETE_WINDOW", close_alert_dialog)

            relative_var = StringVar(value=existing_alert.get("relativeTo", "end"))
            message_box = Text(alert_dialog, height=4, width=36)
            self._style_text(message_box)
            message_box.insert("1.0", existing_alert.get("message", ""))
            keep_var = BooleanVar(value=bool(existing_alert.get("keep", False)))
            minutes_var = StringVar(value=str(existing_alert.get("minutes", 5)))

            relative_group = ttk.LabelFrame(alert_dialog, text="Calculate from")
            relative_group.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 6))
            ttk.Radiobutton(relative_group, text="End of class", variable=relative_var, value="end").pack(anchor="w", padx=8, pady=3)
            ttk.Radiobutton(relative_group, text="Beginning of class", variable=relative_var, value="start").pack(anchor="w", padx=8, pady=3)

            ttk.Label(alert_dialog, text="Message").grid(row=1, column=0, sticky="nw", padx=10, pady=6)
            message_box.grid(row=1, column=1, sticky="ew", padx=10, pady=6)

            keep_check = Checkbutton(alert_dialog, text="Keep alert after firing", variable=keep_var)
            self._style_checkbutton(keep_check)
            keep_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=6)

            ttk.Label(alert_dialog, text="Minutes since start/before end").grid(row=3, column=0, sticky="w", padx=10, pady=6)
            ttk.Spinbox(alert_dialog, from_=0, to=240, textvariable=minutes_var, width=8).grid(row=3, column=1, sticky="w", padx=10, pady=6)
            alert_dialog.grid_columnconfigure(1, weight=1)

            def save_alert():
                try:
                    minutes = int(minutes_var.get().strip())
                    if minutes < 0:
                        raise ValueError("Minutes must be zero or greater.")
                    base_time = entry.end if relative_var.get() == "end" else entry.start
                    class_dt = datetime.combine(class_date, base_time) + timedelta(seconds=state.settings.schedule.delay)
                    alert_dt = class_dt - timedelta(minutes=minutes) if relative_var.get() == "end" else class_dt + timedelta(minutes=minutes)
                    message = message_box.get("1.0", END).strip()
                    payload = {
                        "date": alert_dt.strftime("%Y-%m-%d"),
                        "classDate": date_key,
                        "class": slot,
                        "time": alert_dt.strftime("%H:%M"),
                        "message": message or state.settings.localization.alert.defaultText,
                        "keep": keep_var.get(),
                        "relativeTo": relative_var.get(),
                        "minutes": minutes,
                    }
                    if alert_index is None:
                        state.settings.events._data["alerts"].append(payload)
                    else:
                        state.settings.events._data["alerts"][alert_index] = payload
                    state.settings.events.save()
                    refresh_alerts()
                    self._refresh_clock_runtime()
                    close_alert_dialog()
                except Exception as exc:
                    messagebox.showerror("Invalid alert", str(exc), parent=alert_dialog)

            button_row = ttk.Frame(alert_dialog)
            button_row.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 10))
            ttk.Button(button_row, text="Save", command=save_alert).pack(side="left")
            ttk.Button(button_row, text="Cancel", command=close_alert_dialog).pack(side="left", padx=(6, 0))
            alert_dialog.update_idletasks()
            alert_dialog.geometry(f"{alert_dialog.winfo_reqwidth()}x{alert_dialog.winfo_reqheight()}")

        def edit_selected_alert(_event=None):
            if not alert_list.curselection():
                return
            open_alert_prompt(current_alert_indexes[alert_list.curselection()[0]])

        alert_list.bind("<Double-Button-1>", edit_selected_alert)

        alert_buttons = ttk.Frame(alerts_tab)
        alert_buttons.grid(row=2, column=1, sticky="sew", padx=(0, 8), pady=(0, 8))
        ttk.Button(alert_buttons, text="Remove selected alert", command=remove_alert).pack(fill="x", pady=(0, 6))
        ttk.Button(alert_buttons, text="Add new alert", command=open_alert_prompt).pack(fill="x")
        refresh_alerts()

    def _delete_weekly_slot(self, day_index: int, slot: int, dialog: Toplevel | None = None):
        if day_index < len(state.settings.schedule._data["default"]):
            state.settings.schedule._data["default"][day_index].pop(str(slot), None)
        state.settings.schedule._data["secondary"].get(str(day_index), {}).pop(str(slot), None)
        state.settings.schedule.save()
        if dialog is not None:
            self._close_child_window(dialog)
        else:
            self.after(0, self._focus_window)
        self._refresh_clock_runtime()
        self._openSchedule()

    def _openSpecialDays(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Special days", style="mainText.Label").pack(anchor="w")
        day_list = Listbox(left, exportselection=False, width=18, height=18)
        self._style_listbox(day_list)
        day_list.pack(fill="y", expand=True, pady=(8, 8))
        for key in sorted(state.settings.events._data["specialDays"]):
            day_list.insert(END, key)

        selected_date = StringVar(value=state.getTime().strftime("%Y-%m-%d"))
        full_var = BooleanVar(value=False)
        row_container = ttk.Frame(right)
        row_container.pack(fill="both", expand=True, pady=(8, 0))
        rows: list[dict[str, object]] = []

        def add_row(slot="", start="", end="", value=""):
            row_frame = ttk.Frame(row_container)
            row_frame.pack(fill="x", pady=2)
            slot_var = StringVar(value=str(slot))
            value_var = StringVar(value=value)
            ttk.Entry(row_frame, textvariable=slot_var, width=8).pack(side="left", padx=(0, 4))
            start_frame, start_hour_var, start_minute_var = self._create_time_inputs(row_frame, start=start)
            start_frame.pack(side="left", padx=(0, 4))
            end_frame, end_hour_var, end_minute_var = self._create_time_inputs(row_frame, start=end)
            end_frame.pack(side="left", padx=(0, 4))
            ttk.Entry(row_frame, textvariable=value_var).pack(side="left", fill="x", expand=True, padx=(0, 4))
            ttk.Button(row_frame, text="X", width=3, command=lambda: remove_row(row_frame)).pack(side="left")
            rows.append(
                {
                    "frame": row_frame,
                    "slot": slot_var,
                    "start_hour": start_hour_var,
                    "start_minute": start_minute_var,
                    "end_hour": end_hour_var,
                    "end_minute": end_minute_var,
                    "value": value_var,
                }
            )

        def remove_row(row_frame: ttk.Frame):
            for index, row in enumerate(list(rows)):
                if row["frame"] is row_frame:
                    rows.pop(index)
                    break
            row_frame.destroy()

        def load_special_day(_event=None):
            for row in list(rows):
                row["frame"].destroy()
            rows.clear()
            if not day_list.curselection():
                return
            key = day_list.get(day_list.curselection()[0])
            selected_date.set(key)
            parsed_date = datetime.strptime(key, "%Y-%m-%d").date()
            date_year_var.set(str(parsed_date.year))
            date_month_var.set(f"{parsed_date.month:02}")
            date_day_var.set(f"{parsed_date.day:02}")
            data = state.settings.events._data["specialDays"].get(key, {})
            full_var.set(bool(data.get("full", False)))
            classes = data.get("classes", {}) or {}
            slot_times = data.get("timeSlots", {}) or {}
            slot_keys = sorted({*classes.keys(), *slot_times.keys()}, key=lambda item: int(item))
            for slot_key in slot_keys:
                times = slot_times.get(slot_key, state.settings.schedule._data["timeSlots"].get(slot_key, "-"))
                start, end = times.split("-", 1) if "-" in times else ("", "")
                class_value = self._format_class_value(classes[slot_key]) if slot_key in classes else ""
                add_row(slot_key, start, end, class_value)
            if not slot_keys:
                add_row()

        day_list.bind("<<ListboxSelect>>", load_special_day)

        ttk.Label(right, text="Date").pack(anchor="w")
        date_frame, date_year_var, date_month_var, date_day_var = self._create_date_inputs(right, value=selected_date.get())
        date_frame.pack(anchor="w", pady=(0, 8))
        full_check = Checkbutton(right, text="Replace entire day", variable=full_var)
        self._style_checkbutton(full_check)
        full_check.pack(anchor="w", pady=(0, 8))
        ttk.Label(right, text="Rows: slot | start | end | classes").pack(anchor="w")

        button_bar = ttk.Frame(right)
        button_bar.pack(fill="x", pady=(8, 8))
        ttk.Button(button_bar, text="Add row", command=add_row).pack(side="left")

        def new_special_day():
            try:
                key = self._date_from_vars(date_year_var, date_month_var, date_day_var)
            except ValueError:
                return messagebox.showerror("Invalid date", "Use a valid date.", parent=self)
            selected_date.set(key)
            if key not in day_list.get(0, END):
                day_list.insert(END, key)
            day_list.selection_clear(0, END)
            day_list.selection_set(day_list.size() - 1)
            state.settings.events._data["specialDays"].setdefault(key, {"full": False})
            self._refresh_clock_runtime()
            load_special_day()

        ttk.Button(button_bar, text="New date", command=new_special_day).pack(side="left", padx=(6, 0))

        def save_special_day():
            try:
                key = self._date_from_vars(date_year_var, date_month_var, date_day_var)
            except ValueError:
                return messagebox.showerror("Invalid date", "Use a valid date.", parent=self)
            selected_date.set(key)

            payload: dict[str, object] = {"full": full_var.get()}
            classes: dict[str, object] = {}
            time_slots: dict[str, str] = {}
            try:
                for row in rows:
                    slot = row["slot"].get().strip()
                    if not slot:
                        continue
                    int(slot)
                    start = self._time_from_vars(row["start_hour"], row["start_minute"])
                    end = self._time_from_vars(row["end_hour"], row["end_minute"])
                    value = row["value"].get().strip()
                    time_slots[slot] = f"{start}-{end}"
                    if value:
                        classes[slot] = self._parse_class_entry(value)
            except Exception as exc:
                return messagebox.showerror("Invalid special day", str(exc), parent=self)

            if classes:
                payload["classes"] = classes
            if time_slots:
                payload["timeSlots"] = time_slots
            state.settings.events._data["specialDays"][key] = payload
            state.settings.events.save()
            self._refresh_clock_runtime()
            self._openSpecialDays()

        def delete_special_day():
            if not day_list.curselection():
                return
            key = day_list.get(day_list.curselection()[0])
            state.settings.events._data["specialDays"].pop(key, None)
            state.settings.events.save()
            self._refresh_clock_runtime()
            self._openSpecialDays()

        footer = ttk.Frame(right)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="Save special day", command=save_special_day).pack(side="left")
        ttk.Button(footer, text="Delete", command=delete_special_day).pack(side="left", padx=(6, 0))

        add_row()

    def _openGeneral(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        cfg = state.settings.config
        background_var = StringVar(value=f"#{cfg.background:06X}")
        foreground_var = StringVar(value=f"#{cfg.foreground:06X}")
        lang_options = self._available_languages()
        lang_var = StringVar(value=cfg.lang if cfg.lang in lang_options else (lang_options[0] if lang_options else cfg.lang))
        ignore_updates_var = BooleanVar(value=cfg.ignoreUpdates)
        show_teacher_var = BooleanVar(value=cfg.showTeacher)
        alpha_default_var = StringVar(value=str(cfg.alpha.get("default", 0.75)))
        alpha_hover_var = StringVar(value=str(cfg.alpha.get("onHover", 0.25)))

        fields = ttk.Frame(root)
        fields.pack(fill="x")
        items = [
            ("Background", background_var),
            ("Foreground", foreground_var),
            ("Language", lang_var),
            ("Alpha default", alpha_default_var),
            ("Alpha on hover", alpha_hover_var),
        ]
        for row, (label, var) in enumerate(items):
            ttk.Label(fields, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=4)
            if label == "Language":
                ttk.Combobox(fields, textvariable=var, values=lang_options, state="readonly").grid(row=row, column=1, sticky="ew", padx=4, pady=4)
            else:
                ttk.Entry(fields, textvariable=var).grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        fields.grid_columnconfigure(1, weight=1)
        ignore_updates_check = Checkbutton(fields, text="Ignore updates", variable=ignore_updates_var)
        self._style_checkbutton(ignore_updates_check)
        ignore_updates_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        show_teacher_check = Checkbutton(fields, text="Show teacher", variable=show_teacher_var)
        self._style_checkbutton(show_teacher_check)
        show_teacher_check.grid(row=6, column=0, columnspan=2, sticky="w", padx=4, pady=4)

        def choose_color(target: StringVar):
            color = colorchooser.askcolor(target.get(), parent=self)[1]
            if color:
                target.set(color.upper())

        color_buttons = ttk.Frame(root)
        color_buttons.pack(fill="x", pady=(8, 8))
        ttk.Button(color_buttons, text="Pick background", command=lambda: choose_color(background_var)).pack(side="left")
        ttk.Button(color_buttons, text="Pick foreground", command=lambda: choose_color(foreground_var)).pack(side="left", padx=(6, 0))

        def save_general():
            try:
                bg = background_var.get().strip()
                fg = foreground_var.get().strip()
                if not (bg.startswith("#") and len(bg) == 7):
                    raise ValueError("Background must be #RRGGBB")
                if not (fg.startswith("#") and len(fg) == 7):
                    raise ValueError("Foreground must be #RRGGBB")
                int(bg.removeprefix("#"), 16)
                int(fg.removeprefix("#"), 16)
                cfg._data["background"] = bg.upper()
                cfg._data["foreground"] = fg.upper()
                cfg._data["lang"] = lang_var.get().strip() or cfg._data["lang"]
                cfg._data["ignoreUpdates"] = ignore_updates_var.get()
                cfg._data["showTeacher"] = show_teacher_var.get()
                cfg.setAlpha("default", float(alpha_default_var.get().strip()))
                cfg.setAlpha("onHover", float(alpha_hover_var.get().strip()))
                cfg.save()
                try:
                    state.clock.wm_attributes("-alpha", cfg.alpha["default"])
                except Exception:
                    self.logger.exception("Could not refresh clock colors from settings UI")
                self._openGeneral()
            except Exception as exc:
                messagebox.showerror("Invalid settings", str(exc), parent=self)
            self._refresh_clock_runtime()

        ttk.Button(root, text="Save general settings", command=save_general).pack(anchor="w")

if __name__ == "__main__":
    from sys import path as sp
    from os import path
    sp.append(path.abspath(path.join(path.dirname(__file__), '..')))

from copy import deepcopy
from datetime import date, datetime, timedelta
from logging import getLogger
from tkinter import (
    BooleanVar,
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
            state.openGUIs["settings"].focus_force()
            return self.logger.debug("Settings opened more than once. Focus set to older window")

        super().__init__(state.clock)
        state.openGUIs["settings"] = self
        self.protocol("WM_DELETE_WINDOW", self._closeFunc)

        self.style = ttk.Style(self)
        self.style.configure("mainText.Label", foreground="#FFFFFF", background="#202020")
        self.style.configure("section.TFrame", background="#202020")
        self.style.configure("scheduleElement.TButton", padding=8)
        self.configure(background="#202020")

        loc = state.settings.localization
        self.title(loc.settings.title)
        self.geometry(f"980x720+{self.winfo_screenwidth()//2-490}+{self.winfo_screenheight()//2-360}")

        menu = Menu(self, background="#202020", fg="#FFFFFF", relief="ridge")
        menu.add_command(label=loc.settings.topbar["schedule"], command=self._openSchedule)
        menu.add_command(label=loc.settings.topbar["special_days"], command=self._openSpecialDays)
        menu.add_command(label=loc.settings.topbar["alerts"], command=self._openAlerts)
        menu.add_command(label=loc.settings.topbar["general"], command=self._openGeneral)
        self.config(menu=menu)

        self.content = Frame(self, bg="#202020")
        self.content.pack(fill="both", expand=True, padx=12, pady=12)
        self._openSchedule()

    def _closeFunc(self):
        state.openGUIs.pop("settings", None)
        self.destroy()

    def _clearContent(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _current_week_start(self) -> date:
        today = state.getTime().date()
        return today - timedelta(days=today.weekday())

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

    def _openSchedule(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        week_start = self._current_week_start()
        ttk.Label(root, text=f"Week {week_start.isocalendar().week}", style="mainText.Label").pack(anchor="w")
        ttk.Label(
            root,
            text="Click a class slot to edit the weekly schedule for that day. Use comma-separated class codes for grouped classes.",
            style="mainText.Label",
        ).pack(anchor="w", pady=(0, 12))

        schedule_frame = ttk.Frame(root)
        schedule_frame.pack(fill="x", pady=(0, 18))

        unified = state.settings.schedule.getUnifiedSchedule(week_of=state.getTime())
        for day_index in range(7):
            day_frame = ttk.LabelFrame(schedule_frame, text=(week_start + timedelta(days=day_index)).strftime("%A %Y-%m-%d"))
            day_frame.grid(row=0, column=day_index, sticky="n", padx=4)
            if day_index >= len(unified) or not unified[day_index]:
                ttk.Label(day_frame, text="No classes").pack(fill="x", padx=4, pady=4)
                ttk.Button(day_frame, text="Add slot", command=lambda d=day_index: self._edit_weekly_slot(d)).pack(fill="x", padx=4, pady=4)
                continue
            for entry in sorted(unified[day_index], key=lambda item: item.classIndex):
                label = f"#{entry.classIndex}\n{entry.start.strftime('%H:%M')}-{entry.end.strftime('%H:%M')}\n{self._format_class_value(self._raw_weekly_value(day_index, entry.classIndex))}"
                ttk.Button(
                    day_frame,
                    text=label,
                    style="scheduleElement.TButton",
                    command=lambda d=day_index, s=entry.classIndex: self._edit_weekly_slot(d, s),
                ).pack(fill="x", padx=4, pady=4)
            ttk.Button(day_frame, text="Add slot", command=lambda d=day_index: self._edit_weekly_slot(d)).pack(fill="x", padx=4, pady=4)

        classes_frame = ttk.LabelFrame(root, text="Class Catalog")
        classes_frame.pack(fill="both", expand=True)
        ttk.Label(
            classes_frame,
            text="Add or update class codes used by the schedule editor.",
            style="mainText.Label",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        class_list = Listbox(classes_frame, exportselection=False, height=12)
        class_list.grid(row=1, column=0, rowspan=6, sticky="nsew", padx=(0, 10))
        classes_frame.grid_columnconfigure(1, weight=1)
        classes_frame.grid_rowconfigure(1, weight=1)

        code_var = StringVar()
        name_var = StringVar()
        room_var = StringVar()
        teacher_var = StringVar()

        for code in sorted(state.settings.classes.classes):
            class_list.insert(END, code)

        def load_selected(_event=None):
            if not class_list.curselection():
                return
            code = class_list.get(class_list.curselection()[0])
            data = state.settings.classes.classes.get(code, {})
            code_var.set(code)
            name_var.set(data.get("name", ""))
            room_var.set(data.get("room", ""))
            teacher_var.set(data.get("teacher", ""))

        class_list.bind("<<ListboxSelect>>", load_selected)

        for row, (label, var) in enumerate((("Code", code_var), ("Name", name_var), ("Room", room_var), ("Teacher", teacher_var)), start=1):
            ttk.Label(classes_frame, text=label).grid(row=row, column=1, sticky="w", pady=2)
            ttk.Entry(classes_frame, textvariable=var).grid(row=row, column=2, sticky="ew", pady=2)

        def save_class():
            code = code_var.get().strip()
            if not code:
                return messagebox.showerror("Invalid class", "Code is required.", parent=self)
            state.settings.classes.classes[code] = {
                "name": name_var.get().strip() or code,
                "room": room_var.get().strip(),
                "teacher": teacher_var.get().strip(),
            }
            state.settings.classes.save()
            items = list(class_list.get(0, END))
            if code not in items:
                class_list.insert(END, code)
            self._openSchedule()

        def delete_class():
            if not class_list.curselection():
                return
            code = class_list.get(class_list.curselection()[0])
            if not messagebox.askyesno("Delete class", f"Delete class '{code}'?", parent=self):
                return
            state.settings.classes.classes.pop(code, None)
            state.settings.classes.save()
            self._openSchedule()

        button_row = ttk.Frame(classes_frame)
        button_row.grid(row=5, column=1, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(button_row, text="Save class", command=save_class).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Delete class", command=delete_class).pack(side="left")

    def _raw_weekly_value(self, day_index: int, slot: int):
        schedule_data = state.settings.schedule._data
        is_secondary = state.settings.schedule.currentlySecondaryWeek(state.getTime())
        if is_secondary:
            slot_value = schedule_data["secondary"].get(str(day_index), {}).get(str(slot), None)
            if slot_value is not None or str(slot) in schedule_data["secondary"].get(str(day_index), {}):
                return slot_value
        return schedule_data["default"][day_index].get(str(slot))

    def _edit_weekly_slot(self, day_index: int, slot: int | None = None):
        dialog = Toplevel(self)
        dialog.title(f"Edit {DAY_NAMES[day_index]}")
        dialog.transient(self)
        dialog.grab_set()

        existing_slot = slot if slot is not None else self._next_slot_index()
        value = self._raw_weekly_value(day_index, existing_slot)
        is_secondary = BooleanVar(value=False)
        if str(existing_slot) in state.settings.schedule._data["secondary"].get(str(day_index), {}):
            is_secondary.set(True)

        slot_var = StringVar(value=str(existing_slot))
        value_var = StringVar(value=self._format_class_value(value) if value is not None else "")
        start_var = StringVar()
        end_var = StringVar()
        current_time = state.settings.schedule._data["timeSlots"].get(str(existing_slot), "")
        if current_time:
            start, end = current_time.split("-", 1)
            start_var.set(start)
            end_var.set(end)

        ttk.Label(dialog, text="Slot").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dialog, textvariable=slot_var).grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(dialog, text="Start").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dialog, textvariable=start_var).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(dialog, text="End").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dialog, textvariable=end_var).grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(dialog, text=f"Class code(s) or {NONE_TOKEN}").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dialog, textvariable=value_var).grid(row=3, column=1, sticky="ew", padx=8, pady=4)
        Checkbutton(dialog, text="Save as secondary-week override", variable=is_secondary).grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Label(dialog, text="Available codes: " + ", ".join(sorted(state.settings.classes.classes))).grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        dialog.grid_columnconfigure(1, weight=1)

        def save_slot():
            try:
                slot_index = int(slot_var.get().strip())
                if slot_index <= 0:
                    raise ValueError("Slot must be positive")
                start = self._parse_timestring(start_var.get())
                end = self._parse_timestring(end_var.get())
                parsed = self._parse_class_entry(value_var.get())
            except Exception as exc:
                return messagebox.showerror("Invalid slot", str(exc), parent=dialog)

            state.settings.schedule._data["timeSlots"][str(slot_index)] = f"{start}-{end}"
            target = state.settings.schedule._data["secondary"].setdefault(str(day_index), {}) if is_secondary.get() else state.settings.schedule._data["default"][day_index]
            target[str(slot_index)] = parsed
            if not is_secondary.get():
                state.settings.schedule._data["secondary"].get(str(day_index), {}).pop(str(slot_index), None)
            state.settings.schedule.save()
            dialog.destroy()
            self._openSchedule()

        def delete_slot():
            state.settings.schedule._data["default"][day_index].pop(str(existing_slot), None)
            state.settings.schedule._data["secondary"].get(str(day_index), {}).pop(str(existing_slot), None)
            state.settings.schedule.save()
            dialog.destroy()
            self._openSchedule()

        button_row = ttk.Frame(dialog)
        button_row.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        ttk.Button(button_row, text="Save", command=save_slot).pack(side="left")
        ttk.Button(button_row, text="Delete", command=delete_slot).pack(side="left", padx=(6, 0))

    def _next_slot_index(self) -> int:
        keys = {int(key) for key in state.settings.schedule._data["timeSlots"].keys()} if state.settings.schedule._data["timeSlots"] else set()
        return max(keys, default=0) + 1

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
        day_list.pack(fill="y", expand=True, pady=(8, 8))
        for key in sorted(state.settings.events._data["specialDays"]):
            day_list.insert(END, key)

        selected_date = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        full_var = BooleanVar(value=False)
        row_container = ttk.Frame(right)
        row_container.pack(fill="both", expand=True, pady=(8, 0))
        rows: list[dict[str, object]] = []

        def add_row(slot="", start="", end="", value=""):
            row_frame = ttk.Frame(row_container)
            row_frame.pack(fill="x", pady=2)
            slot_var = StringVar(value=str(slot))
            start_var = StringVar(value=start)
            end_var = StringVar(value=end)
            value_var = StringVar(value=value)
            ttk.Entry(row_frame, textvariable=slot_var, width=8).pack(side="left", padx=(0, 4))
            ttk.Entry(row_frame, textvariable=start_var, width=8).pack(side="left", padx=(0, 4))
            ttk.Entry(row_frame, textvariable=end_var, width=8).pack(side="left", padx=(0, 4))
            ttk.Entry(row_frame, textvariable=value_var).pack(side="left", fill="x", expand=True, padx=(0, 4))
            ttk.Button(row_frame, text="X", width=3, command=lambda: remove_row(row_frame)).pack(side="left")
            rows.append({"frame": row_frame, "slot": slot_var, "start": start_var, "end": end_var, "value": value_var})

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

        ttk.Label(right, text="Date (YYYY-MM-DD)").pack(anchor="w")
        ttk.Entry(right, textvariable=selected_date).pack(fill="x", pady=(0, 8))
        Checkbutton(right, text="Replace entire day", variable=full_var).pack(anchor="w", pady=(0, 8))
        ttk.Label(right, text="Rows: slot | start | end | classes").pack(anchor="w")

        button_bar = ttk.Frame(right)
        button_bar.pack(fill="x", pady=(8, 8))
        ttk.Button(button_bar, text="Add row", command=add_row).pack(side="left")

        def new_special_day():
            key = selected_date.get().strip()
            try:
                datetime.strptime(key, "%Y-%m-%d")
            except ValueError:
                return messagebox.showerror("Invalid date", "Use YYYY-MM-DD.", parent=self)
            if key not in day_list.get(0, END):
                day_list.insert(END, key)
            day_list.selection_clear(0, END)
            day_list.selection_set(END)
            state.settings.events._data["specialDays"].setdefault(key, {"full": False})
            load_special_day()

        ttk.Button(button_bar, text="New date", command=new_special_day).pack(side="left", padx=(6, 0))

        def save_special_day():
            key = selected_date.get().strip()
            try:
                datetime.strptime(key, "%Y-%m-%d")
            except ValueError:
                return messagebox.showerror("Invalid date", "Use YYYY-MM-DD.", parent=self)

            payload: dict[str, object] = {"full": full_var.get()}
            classes: dict[str, object] = {}
            time_slots: dict[str, str] = {}
            try:
                for row in rows:
                    slot = row["slot"].get().strip()
                    if not slot:
                        continue
                    int(slot)
                    start = row["start"].get().strip()
                    end = row["end"].get().strip()
                    value = row["value"].get().strip()
                    if start and end:
                        time_slots[slot] = f"{self._parse_timestring(start)}-{self._parse_timestring(end)}"
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
            self._openSpecialDays()

        def delete_special_day():
            if not day_list.curselection():
                return
            key = day_list.get(day_list.curselection()[0])
            state.settings.events._data["specialDays"].pop(key, None)
            state.settings.events.save()
            self._openSpecialDays()

        footer = ttk.Frame(right)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="Save special day", command=save_special_day).pack(side="left")
        ttk.Button(footer, text="Delete", command=delete_special_day).pack(side="left", padx=(6, 0))

        add_row()

    def _openAlerts(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Alerts", style="mainText.Label").pack(anchor="w")
        ttk.Label(root, text="Set an alert time, optional date or weekday, and an optional message.", style="mainText.Label").pack(anchor="w", pady=(0, 12))

        alert_list = Listbox(root, exportselection=False, height=12)
        alert_list.pack(fill="x", pady=(0, 12))
        for alert in state.settings.events._data["alerts"]:
            target = alert.get("date", f"weekday={alert.get('weekday', 'daily')}")
            alert_list.insert(END, f"{alert['time']} | {target} | {alert.get('message', '')}")

        form = ttk.Frame(root)
        form.pack(fill="x")
        time_var = StringVar()
        date_var = StringVar()
        weekday_var = StringVar()
        keep_var = BooleanVar(value=False)
        ttk.Label(form, text="Time (HH:MM)").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=time_var).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=date_var).grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(form, text="Weekday 0-6").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=weekday_var).grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        Checkbutton(form, text="Keep recurring alert", variable=keep_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ttk.Label(form, text="Message").grid(row=4, column=0, sticky="nw", padx=4, pady=4)
        message_box = Text(form, height=4, width=40)
        message_box.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        form.grid_columnconfigure(1, weight=1)

        def save_alert():
            try:
                time_value = self._parse_timestring(time_var.get())
                payload = {"time": time_value, "keep": keep_var.get()}
                message = message_box.get("1.0", END).strip()
                if message:
                    payload["message"] = message
                if date_var.get().strip():
                    payload["date"] = datetime.strptime(date_var.get().strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
                elif weekday_var.get().strip():
                    weekday_value = int(weekday_var.get().strip())
                    if weekday_value not in range(7):
                        raise ValueError("Weekday must be between 0 and 6.")
                    payload["weekday"] = weekday_value
                state.settings.events._data["alerts"].append(payload)
                state.settings.events.save()
                self._openAlerts()
            except Exception as exc:
                messagebox.showerror("Invalid alert", str(exc), parent=self)

        def delete_alert():
            if not alert_list.curselection():
                return
            index = alert_list.curselection()[0]
            state.settings.events._data["alerts"].pop(index)
            state.settings.events.save()
            self._openAlerts()

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Save alert", command=save_alert).pack(side="left")
        ttk.Button(buttons, text="Delete selected", command=delete_alert).pack(side="left", padx=(6, 0))

    def _openGeneral(self):
        self._clearContent()
        root = ttk.Frame(self.content)
        root.pack(fill="both", expand=True)

        cfg = state.settings.config
        background_var = StringVar(value=f"#{cfg.background:06X}")
        foreground_var = StringVar(value=f"#{cfg.foreground:06X}")
        lang_var = StringVar(value=cfg.lang)
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
            ttk.Entry(fields, textvariable=var).grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        fields.grid_columnconfigure(1, weight=1)
        Checkbutton(fields, text="Ignore updates", variable=ignore_updates_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        Checkbutton(fields, text="Show teacher", variable=show_teacher_var).grid(row=6, column=0, columnspan=2, sticky="w", padx=4, pady=4)

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
                    state.clock.changeColors(bg=bg.upper(), fg=fg.upper())
                    state.clock.wm_attributes("-alpha", cfg.alpha["default"])
                except Exception:
                    self.logger.exception("Could not refresh clock colors from settings UI")
                self._openGeneral()
            except Exception as exc:
                messagebox.showerror("Invalid settings", str(exc), parent=self)

        ttk.Button(root, text="Save general settings", command=save_general).pack(anchor="w")

import tkinter as tk

def add_channel(self):
    num = self.channel_num_entry.get().strip()
    label = self.channel_label_entry.get().strip()

    if not num.isdigit():
        self.status_label.config(text="Channel number must be an integer.")
        return

    num = int(num)

    if label == "":
        self.status_label.config(text="Enter a channel label.")
        return

    for ch in self.channels:
        if ch["num"] == num:
            self.status_label.config(text=f"Channel {num} already exists.")
            return

    self.channels.append({"num": num, "label": label})
    self.channels.sort(key=lambda x: x["num"])

    self.update_channel_listbox()

    self.channel_num_entry.delete(0, tk.END)
    self.channel_label_entry.delete(0, tk.END)

    self.status_label.config(text="Channel added.")


def remove_channel(self):
    num = self.channel_num_entry.get().strip()

    if not num.isdigit():
        self.status_label.config(text="Channel number must be an integer.")
        return

    num = int(num)

    new_list = [ch for ch in self.channels if ch["num"] != num]

    if len(new_list) == len(self.channels):
        self.status_label.config(text=f"Channel {num} not found.")
        return

    self.channels = new_list

    self.update_channel_listbox()

    self.channel_num_entry.delete(0, tk.END)
    self.channel_label_entry.delete(0, tk.END)

    self.status_label.config(text="Channel removed.")


def update_channel_listbox(self):

    self.channel_listbox.delete(0, tk.END)

    for ch in self.channels:
        self.channel_listbox.insert(
            tk.END,
            f"Channel {ch['num']} — {ch['label']}"
        )

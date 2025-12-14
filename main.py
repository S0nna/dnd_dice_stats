import tkinter as tk
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

possibleDice: list[int] = [4, 6, 8, 10, 12, 20, 100]
list_of_lists: list[list[tuple[datetime, int]]] = [[] for _ in possibleDice]
all_time_rolls: list[list[tuple[datetime, int]]] = [[] for _ in possibleDice]
all_time_averages: list[float] = [0.0] * len(possibleDice)
SAVE_FILE: Path = Path("dice_stats.json")

def averageList(passedList: list[tuple[datetime, int]]) -> float:
    realElements: list[int] = [roll for ts, roll in passedList]
    try:
        return sum(realElements) / len(realElements)
    except ZeroDivisionError:
        return 0.0

def load_all_time_data() -> None:
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, 'r') as f:
                data: dict = json.load(f)
                all_time_rolls: list[list[tuple[datetime, int]]] = []
                for dice_data in data.get('all_time_rolls', [[] for _ in possibleDice]):
                    dice_rolls: list[tuple[datetime, int]] = []
                    for ts_str, roll in dice_data:
                        try:
                            ts: datetime = datetime.fromisoformat(ts_str)
                            dice_rolls.append((ts, int(roll)))
                        except ValueError:
                            pass
                    all_time_rolls.append(dice_rolls)
                
                all_time_averages: list[float] = data.get('all_time_averages', [0.0] * len(possibleDice))
        except json.JSONDecodeError:
            pass

def save_all_time_data() -> None:
    data: dict = {
        'all_time_averages': all_time_averages,
        'all_time_rolls': [[(r[0].isoformat(), r[1]) for r in rolls] for rolls in all_time_rolls],
        'session_rolls': [[(r[0].isoformat(), r[1]) for r in rolls] for rolls in list_of_lists]
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class GUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Dice Roller with Time Tracking & Graphs")
        
        self.entries: dict[int, tk.Entry] = {}
        self.sessionLabels: list[tk.Label] = []
        self.allTimeLabels: list[tk.Label] = []
        
        load_all_time_data()
        
        main_frame: tk.Frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for index, dice in enumerate(possibleDice):
            index: int
            dice: int

            diceLabel: tk.Label = tk.Label(main_frame, text=f"d{dice}", font=("Arial", 10, "bold"))
            sessionLabel: tk.Label = tk.Label(main_frame, text="Session Avg = 0")
            allTimeLabel: tk.Label = tk.Label(main_frame, text=f"All-time Avg = {all_time_averages[index]:.2f}")
            
            entry: tk.Entry = tk.Entry(main_frame, width=15)
            self.entries[index] = entry
            self.sessionLabels.append(sessionLabel)
            self.allTimeLabels.append(allTimeLabel)
            
            diceLabel.grid(row=index, column=0, sticky="w", padx=5, pady=2)
            entry.grid(row=index, column=1, sticky="w", padx=5, pady=2)
            sessionLabel.grid(row=index, column=2, sticky="w", padx=5, pady=2)
            allTimeLabel.grid(row=index, column=3, sticky="w", padx=5, pady=2)
            
            entry.bind("<Return>", lambda event, idx=index: self.updateRolls())
        
        button_frame: tk.Frame = tk.Frame(main_frame)
        button_frame.grid(row=len(possibleDice), column=0, columnspan=4, pady=20)
        
        submit_button: tk.Button = tk.Button(button_frame, text="Submit Rolls", command=self.updateRolls, bg="#4CAF50", fg="white")
        submit_button.pack(side=tk.LEFT, padx=5)
        
        export_button: tk.Button = tk.Button(button_frame, text="Export & Graph", command=self.export_and_graph, bg="#2196F3", fg="white")
        export_button.pack(side=tk.LEFT, padx=5)
    
    def updateRolls(self) -> None:
        current_time: datetime = datetime.now()
        
        for index, entry in self.entries.items():
            index: int
            entry: tk.Entry

            input_value: str = entry.get()
            input_values: list[str] = input_value.replace(",", " ").split()
            
            for value in input_values:
                value: str

                try:
                    dice_value: int = int(value)
                    roll_data: tuple[datetime, int] = (current_time, dice_value)
                    list_of_lists[index].append(roll_data)
                    all_time_rolls[index].append(roll_data)
                    
                    all_time_averages[index] = averageList(all_time_rolls[index])
                    
                except ValueError:
                    pass
            
            entry.delete(0, tk.END)
        
        for index in range(len(list_of_lists)):
            index: int

            session_avg: float = averageList(list_of_lists[index])
            all_time_avg: float = all_time_averages[index]
            
            self.sessionLabels[index].config(text=f"Session Avg = {session_avg:.2f}")
            self.allTimeLabels[index].config(text=f"All-time Avg = {all_time_avg:.2f}")
    
    def export_and_graph(self) -> None:
        save_all_time_data()
        
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        fig.suptitle('Dice Rolling Performance Over Time', fontsize=16, fontweight='bold')
        
        for i, dice in enumerate(possibleDice):
            i: int
            dice: int

            row: int = i // 4
            col: int = i % 4
            
            ax = axes[row, col]
            
            if all_time_rolls[i]:
                times: list[datetime] = [r[0] for r in all_time_rolls[i]]
                rolls: list[int] = [r[1] for r in all_time_rolls[i]]
                
                ax.plot(times, rolls, 'o-', markersize=4, linewidth=1, alpha=0.7)
                
                expected_avg: float = (1 + dice) / 2
                ax.axhline(y=expected_avg, color='r', linestyle='--', alpha=0.8, label=f'Expected: {expected_avg:.1f}')
                
                ax.set_title(f'd{dice}\nAvg: {averageList(all_time_rolls[i]):.2f}')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            else:
                ax.text(0.5, 0.5, f'No d{dice} rolls yet', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'd{dice}')
        
        plt.tight_layout()
        plt.show()
        
        summary_window: tk.Toplevel = tk.Toplevel(self)
        summary_window.title("Export Complete")
        summary_window.geometry("500x400")
        
        summary_text: tk.Text = tk.Text(summary_window, wrap=tk.WORD)
        summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        summary_content: str = "Stats exported to dice_stats.json\n\n"
        for index, dice in enumerate(possibleDice):
            index: int
            dice: int

            session_avg: float = averageList(list_of_lists[i])
            all_time_avg: float = averageList(all_time_rolls[i])
            summary_content += f"d{dice}: Session={session_avg:.2f}, All-time={all_time_avg:.2f}, Rolls={len(all_time_rolls[i])}\n"
        
        summary_text.insert(tk.END, summary_content)
        summary_text.config(state=tk.DISABLED)
        
        tk.Button(summary_window, text="Close", command=summary_window.destroy).pack(pady=10)

if __name__ == "__main__":
    app: GUI = GUI()
    app.mainloop()

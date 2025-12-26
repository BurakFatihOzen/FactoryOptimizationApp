\# 🏭 Hybrid Production Line Optimization Simulation



This project is a high-performance industrial simulation system developed using \*\*C++ (Backend)\*\* and \*\*Python (Frontend)\*\*. It demonstrates how hybrid algorithms can solve complex manufacturing problems like job scheduling, production planning, and logistics.



\## 🚀 Key Features



\* \*\*Job Scheduling (Sorting):\*\* Minimizes machine setup times using \*\*Quick Sort\*\* (compared with Insertion Sort for performance analysis).

\* \*\*Production Planning (Knapsack):\*\* Maximizes production profit within limited time/capacity using \*\*Dynamic Programming\*\* (vs Greedy approach).

\* \*\*Logistics \& Routing:\*\* Calculates the shortest and most energy-efficient path for factory logistics using \*\*Dijkstra's Algorithm\*\*.

\* \*\*Inventory Management:\*\* Performs instant stock querying using \*\*Binary Search\*\* ($O(\\log N)$).



\## 📂 Project Structure



\* \*\*`src/`\*\*: Source codes (Python \& C++) for developers and code review.

\* \*\*`bin/`\*\*: Ready-to-run standalone application (EXE \& DLL).



\## ⚡ How to Run



\### Method 1: Run Executable (No Python Required)

If you want to test the simulation immediately:

1\.  Navigate to the \*\*`bin`\*\* folder.

2\.  Double-click \*\*`dashboard\_app.exe`\*\*.

3\.  \*⚠️ Important: Ensure `liboptimization\_engine.dll` is in the same folder as the exe.\*



\### Method 2: Run from Source Code

1\.  Install the required Python libraries:

&nbsp;   ```bash

&nbsp;   pip install -r requirements.txt

&nbsp;   ```

2\.  Run the Python interface:

&nbsp;   ```bash

&nbsp;   python src/dashboard\_app.pyw

&nbsp;   ```



\## 🛠️ Tech Stack

\* \*\*Core Engine:\*\* C++17 (Compiled as Dynamic Link Library - DLL)

\* \*\*User Interface:\*\* Python (CustomTkinter)

\* \*\*Data Visualization:\*\* Matplotlib, NetworkX




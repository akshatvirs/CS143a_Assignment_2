# CS 143A Project 2

## 1. Introduction

In this programming assignment, you will be building off your previous implementation in project 1. You must implement additional kernel syscalls and cpu interrupts. By the end of the project, you will implement a few more CPU scheduling algorithms.

**Programming language:** The assignment will be implemented in Python.

**Cooperation and third party code:** This is a **group** programming assignment, and your group should implement the code on your own. Your group may not share final solutions with anyone outside of your group, and your group must write up your own work, expressing it in your own words/notation. Third party code including libraries are not allowed (built in python libraries are fine).

## 2. Environment setup

The simulator runs using standard Python without any installed libraries. Your code will be graded with **Python 3.10.12**, so we recommend using [conda](https://docs.conda.io/en/latest/) to create an environment with exactly that version. If you do not have conda yet, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

If you already created the `cs143a` environment for project 1, you can reuse it: just run `conda activate cs143a`. Otherwise, from the project folder (the one containing `requirements.txt`), create and activate the environment:

```
conda create --name cs143a --file requirements.txt
conda activate cs143a
python --version   # should print Python 3.10.12
```

Activate the environment (`conda activate cs143a`) every time you open a new terminal to work on the project.

You should avoid writing any code that is OS dependent as no test will require this and it could cause problems when grading.

## 3. Updating your code base

### 3.0 Starting point

Since this project builds on the previous one, you may use your old code as a starting point. If you do this, you must make some changes described in the next section. If you were unable to complete the first project or do not wish to use your original code, you may use a provided implementation of project 1 which you can find [here](https://drive.google.com/file/d/1TevzPgMa64nHk4sSYTa8oK9PWBvgQmrx/view?usp=sharing). It is highly recommended that you use your own code as a starting point as this will likely be easier.

### 3.1 Downloading the code

This project uses an upgraded simulator and has new simulations. The previous simulator **will not** be compatible with these new simulations. You can find the new simulator and the new simulations [here](https://drive.google.com/file/d/11U_ehb2gWzU0vEXc0YauY1X_7VBkdapw/view?usp=sharing). You will want to replace the project 1 **`simulator.py`** with the new one you can find in the zip file. Additionally, replace all simulations and correct output with those in the zip file as well.

### 3.2 Updates to `kernel.py`

There are a few changes that need to be made to your **`kernel.py`** file. If these changes are not made, the simulator **will not** work. All changes are for the `Kernel` class in **`kernel.py`**. (If you use the provided implementation of project 1, all of the following changes will have been made already.)

The list of changes include changes to:

- `new_process_arrived`

And a set of new methods:

- `syscall_set_priority`
- `timer_interrupt`

The actual changes:

**old**:

```python
def new_process_arrived(self, new_process: PID) -> PID:
```

**new**:

```python
def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
```

Process type and priority are added as an argument to `new_process_arrived`. This will be used when implementing the multilevel scheduler and priority scheduler. `process_type` can be either `"Foreground"` or `"Background"` depending on the type of the new process. This value can be ignored for FCFS, Priority and RR schedulers. `priority` represents the new process's priority and is ignored by FCFS and RR.

**Entirely new methods (copy paste them at the bottom of your `kernel.py` class):**

```python
# This method is triggered when the currently running process requests to change its priority.
# DO NOT rename or delete this method. DO NOT change its arguments.
def syscall_set_priority(self, new_priority: int) -> PID:
    self.running.priority = new_priority
    self.choose_next_process()
    return self.running.pid

# This function represents the hardware timer interrupt.
# It is triggered every 10 milliseconds and is the only way a kernel can track passing time.
# Do not use real time to track how much time has passed as time is simulated.
# DO NOT rename or delete this method. DO NOT change its arguments.
def timer_interrupt(self) -> PID:
    return self.running.pid
```

### 3.3 Tracking Time

The only way for a kernel to track short periods of time is by counting clock cycles, external timers, or internal registers managed by the CPU. For this simulator, we will keep track of time using the `timer_interrupt`. This interrupt handler is called every 10 milliseconds. As previously mentioned, the built in python time APIs will not be helpful in this simulator as **time is simulated and is not real time**. For this reason, the timer interrupt is the only way for your kernel to keep track of time. Tracking time will be necessary for your implementation of the Multilevel and Round Robin schedulers. However, since the kernel can only keep track of time in 10 millisecond increments, this has some interesting consequences when implementing these algorithms which will be discussed in their implementation sections.

## 4. What to implement

### 4.1 Priority

Implement a **preemptive** priority scheduler. The process with the highest priority should always be running (the highest priority process has the **highest** priority number, e.g. the process with priority 20 should be run before running a process with priority 5). In the case of a tie, the process with the lowest PID should be run. Whenever a new process arrives, or the running process changes its own priority with `syscall_set_priority`, apply the rule above again to all processes, including the running one. If a different process should now be running, switch to it immediately, without waiting for the running process to exit. The preempted process goes back to waiting and will run again once it is chosen by the same rule.

### 4.2 Round Robin scheduler (RR)

You must implement a Round Robin scheduling algorithm with a time quantum of 40 milliseconds. Your kernel cannot read a clock, so it measures time by counting timer interrupts (see 3.3). Use these rules:

- Every timer interrupt counts as 10 ms of running time for whichever process is running when it fires, even if that process was switched in only a moment ago. In other words, assume the running process has been running since the previous timer interrupt.
- On the 4th timer interrupt a process receives (4 × 10 ms = 40 ms), its quantum is used up: move it to the back of the ready queue and run the process at the front. If no other process is waiting, it keeps running and starts a new quantum.
- New arrivals do not preempt. A newly arrived process joins the back of the ready queue.
- Events in the same millisecond are handled in this order: process exits, then process arrivals, then the timer interrupt. So a process that arrives at the same moment a quantum expires is queued ahead of the preempted process.

Consider the following case in `RR1.json`:

```
0.880s : Context switching to pid: 1

0.895s : Process 1 has finished execution and is exiting
0.895s : Context switching to pid: 3

0.930s : Context switching to pid: 2
```

Here the correct output may look a little strange. After process 1 finishes execution, it switches to process 3. However, process 3 does not run for the full 40 milliseconds. It only runs for 35 milliseconds. This becomes a little more clear if we add the timer interrupts to the logs which you can do with the logger.

```
0.880s # Timer interrupt
0.880s : Context switching to pid: 1

0.890s # Timer interrupt

0.895s : Process 1 has finished execution and is exiting
0.895s : Context switching to pid: 3

0.900s # Timer interrupt

0.910s # Timer interrupt

0.920s # Timer interrupt

0.930s # Timer interrupt
0.930s : Context switching to pid: 2
```

As you can see, process 1 finishes in between two timer interrupts. Since they are our only way of keeping track of time, there is no way for the kernel to know if process 3 has been running for 10ms, 5ms, 1ms, etc. when the next timer interrupt happens at 0.900s. For our implementation, you should always assume the process has been running for the full 10 milliseconds. This is why process 3 gets context switched early by 5 milliseconds.

An even more extreme example can be seen in RR2 where an interrupt happens **right after** a context switch.

```
1.790s # Timer interrupt
1.790s : Context switching to pid: 4

1.800s # Timer interrupt

1.810s # Timer interrupt

1.820s # Timer interrupt

1.830s : Process 4 has finished execution and is exiting
1.830s : Context switching to pid: 5
1.830s # Timer interrupt

1.840s # Timer interrupt

1.850s # Timer interrupt

1.860s # Timer interrupt
1.860s : Context switching to pid: 7
```

In this example, even though process 5 has barely executed at all by the time the timer interrupt occurs, the RR scheduler will assume that it has been running for 10 milliseconds. This results in it only running for 30 milliseconds.

### 4.3 Multilevel Scheduler

You must implement a Multilevel scheduling algorithm with 2 levels. The first level is Foreground and the second is Background. Each level operates independently of the other and with different scheduling algorithms.

- **Foreground Level:** This level will use the RR scheduling algorithm. Processes with `process_type == "Foreground"` should be placed in this level and scheduled via the RR scheduling algorithm as described above.
- **Background Level:** This level will use the FCFS scheduling algorithm implemented in project 1. Processes with `process_type == "Background"` should be placed in this level and scheduled via the FCFS scheduling algorithm.
- **Switching Levels:** Your scheduler will switch between running processes in the Foreground level and processes in the Background level. 50% of the time it will run processes in the Foreground and 50% of the time it will run processes in the Background. It should switch between levels every 200 milliseconds. If there are no processes in the other level, it should not switch. When the scheduling algorithm switches to another level, it should stay committed to that level until there are no more processes to run in that level, or 190-200 milliseconds have passed (the range is due to the exact same reasons as the range of 30-40 milliseconds in RR scheduling). If you try to switch to another level and there are no processes to run in that level, you should continue running your current level and begin another 190-200 milliseconds commitment.

## 5. Submitting

When submitting your code you should ONLY submit **`kernel.py`**. It must have this exact name. Upload this file to Gradescope. If after submitting you are unsatisfied with your score, you may submit again as many times as you like. We will only grade the most recent submission.

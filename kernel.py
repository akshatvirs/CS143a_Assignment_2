### Fill in the following information before submitting
# Group id: 52
# Members: Akshatvir Singh, Navaneeth Sujith, Samuel Cook



from collections import deque

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID
    priority: int
    process_type: str

    def __init__(self, pid: PID, priority: int, process_type: str = "Foreground"):
        self.pid = pid
        self.priority = priority
        self.process_type = process_type


# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]
    running: PCB
    idle_pcb: PCB

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # logger is provided which allows you to include your own print statements in the
    #   output logs. These will not impact grading. This can be done with its .log method
    #   which accepts a string.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = deque()
        self.waiting_queue = deque()
        self.idle_pcb = PCB(0, 0, "Idle")
        self.running = self.idle_pcb
        self.ticks = 0 # to count interrupts received by process in RR

        # Multilevel scheduler state
        self.foreground_queue = deque()
        self.background_queue = deque()
        self.foreground_ticks = 0
        self.overall_ticks = 0

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        pcb = PCB(new_process, priority, process_type)

        if self.scheduling_algorithm == "Multilevel":

            if self.running is self.idle_pcb:

                self.running = pcb
                
                self.overall_ticks = 0

                if process_type == "Foreground":
            
                    self.foreground_ticks = 0
            else:
                if process_type == "Foreground":
                    self.foreground_queue.append(pcb)
                else:
                    self.background_queue.append(pcb)

            return self.running.pid

        self.ready_queue.append(pcb)
        self.choose_next_process()
        return self.running.pid  

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            if self.running.process_type == "Foreground":
                if self.foreground_queue:
                    self.running = self.foreground_queue.popleft()
                    self.foreground_ticks = 0
                elif self.background_queue:
                    self.running = self.background_queue.popleft()
                    self.overall_ticks = 0
                else:
                    self.running = self.idle_pcb
                    self.overall_ticks = 0
            elif self.running.process_type == "Background":
                if self.background_queue:
                    self.running = self.background_queue.popleft()
                elif self.foreground_queue:
                    self.running = self.foreground_queue.popleft()
                    self.overall_ticks = 0
                else:
                    self.running = self.idle_pcb
                    self.overall_ticks = 0
            return self.running.pid

        self.running = self.idle_pcb
        self.choose_next_process()
        return self.running.pid
    
    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        if self.scheduling_algorithm != "Multilevel":
            self.choose_next_process()
        return self.running.pid

    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self):
        if len(self.ready_queue) == 0:
            return
        
        if self.scheduling_algorithm == "FCFS":
            if self.running is self.idle_pcb:
                self.running = self.ready_queue.popleft()
        elif self.scheduling_algorithm == "Priority":
            candidates = list(self.ready_queue)
            if self.running is not self.idle_pcb:
                candidates.append(self.running)

            if not candidates:
                self.running = self.idle_pcb
                return

            best_pcb = candidates[0]

            for p in candidates[1:]:
                if p.priority > best_pcb.priority:
                    best_pcb = p
                elif p.priority == best_pcb.priority:
                    if p.pid < best_pcb.pid:
                        best_pcb = p

            if best_pcb is self.running:
                return
            if self.running is not self.idle_pcb:
                self.ready_queue.append(self.running)
            self.ready_queue.remove(best_pcb)
            self.running = best_pcb   
        elif self.scheduling_algorithm == "RR":
            if self.running is self.idle_pcb:
                self.running = self.ready_queue.popleft()
                self.ticks = 0  
        else:
            print("Unknown scheduling algorithm")

    # This method represents the hardware timer interrupt.
    # It is triggered every 10 milliseconds and is the only way our kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def timer_interrupt(self) -> PID:
        if self.scheduling_algorithm == "RR":
            self.ticks += 1
            if self.ticks >= 4:
                self.ticks = 0
                if self.ready_queue:
                    self.ready_queue.append(self.running)
                    self.running = self.ready_queue.popleft()
        elif self.scheduling_algorithm == "Multilevel":
            if self.running is self.idle_pcb:
                return self.running.pid

            if self.running.process_type == "Foreground":
                self.foreground_ticks += 1
                if self.foreground_ticks >= 4:
                    self.foreground_ticks = 0
                    if self.foreground_queue:
                        self.foreground_queue.append(self.running)
                        self.running = self.foreground_queue.popleft()

                self.overall_ticks += 1
                if self.overall_ticks >= 20:
                    if self.background_queue:
                        self.foreground_queue.appendleft(self.running)
                        self.running = self.background_queue.popleft()
                        self.overall_ticks = 0
                    else:
                        self.overall_ticks = 0
            elif self.running.process_type == "Background":
                self.overall_ticks += 1
                if self.overall_ticks >= 20:
                    if self.foreground_queue:
                        self.background_queue.appendleft(self.running)
                        self.running = self.foreground_queue.popleft()
                        self.overall_ticks = 0
                    else:
                        self.overall_ticks = 0

        return self.running.pid

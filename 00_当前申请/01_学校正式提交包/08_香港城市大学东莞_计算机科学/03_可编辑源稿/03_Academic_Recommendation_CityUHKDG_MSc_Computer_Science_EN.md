# Recommendation Letter — Academic Advisor

Shenzhen Technology University

Date: 21 September 2026

Dear Members of the Admissions Committee,
I am writing to support Yongyi Lai’s application to the MSc in Computer Science at City University of Hong Kong (Dongguan).

I am Associate Dean in the School of Artificial Intelligence at Shenzhen Technology University, where Yongyi is a final-year student in Computer Science and Technology. I have known Yongyi since 2023, first as the instructor of University Computer Science A, and since then as the supervisor of two robotics projects in my laboratory. I have also followed Yongyi's competition and independent work closely, and this letter draws on all three.

Yongyi first came to my attention as a strong student who deliberately extended a Computer Science background into robotics. Yongyi ranks 6th in a cohort of 156 students. What stood out was that Yongyi had taken Principles of Automatic Control and Modern Control Theory in addition to the major curriculum, and then applied that preparation to real robot projects. This combination of computing ability and purposeful study in control theory was the basis on which Yongyi took on the two projects I describe below.

The first project, a wheel-legged robot with variable leg length, tested this preparation under changing mechanical geometry: the balance controller had to remain effective as the robot's leg configuration changed. Yongyi constructed the body-pitch and motion states from IMU, wheel-speed and joint feedback, implemented an LQR controller with gains scheduled by leg length, and added a virtual model controller that derived virtual leg length and posture from the closed-chain leg kinematics and mapped support force and pitch torque to the joints through the Jacobian. The controller was integrated and tuned on the physical robot, running on an STM32H7/FreeRTOS platform with FDCAN. The robot kept its body balanced and tracked velocity commands while its legs extended and retracted. The tuning process mattered to me as much as the result: when balance failed, Yongyi located the causes in state inconsistency, torque limits and ground-contact transitions and corrected each in turn, demonstrating a disciplined approach to diagnosing a physical system.

The second project expanded this work from locomotion to navigation. On a car-like mobile robot, Yongyi was responsible for the autonomy chain: EKF/AMCL localisation fusing IMU, wheel encoders and 2D LiDAR, including the handling of timing and coordinate-frame inconsistencies that cause pose jumps; Hybrid-A* global planning under the vehicle's kinematic constraints; TEB local trajectory optimisation; and an MPC tracking controller on a car-like kinematic model. The system ran on the physical vehicle and achieved autonomous navigation from localisation through obstacle-aware planning to trajectory tracking. In my experience, it is unusual at undergraduate level for a student to take responsibility for work spanning localisation, planning and control and carry it through to a functioning vehicle.

I have also seen the same capabilities in work I did not supervise directly but followed closely. In the university RoboMaster team Yongyi was responsible for the embedded control of the hero robot, implementing the gimbal, launcher and chassis control loops on STM32F407/FreeRTOS over CAN; the robot competed in the 2025 national final, where the team won third prize, and the team also took second prize in the 3V3 league. Yongyi also designed and built, alone, an OpenHarmony smart gardening system and demonstrated it to me: it runs YOLOv5 inference on an RK3588 edge device, makes decisions through a LangGraph agent chain and controls irrigation on a Hi3861 device, a complete loop from perception to actuation.

Taken together, these four pieces of work show a student who can move from control theory to embedded implementation and back, who finishes systems rather than components, and who treats documentation and hardware safety as part of the design. They also show where project work stops. In both laboratory projects Yongyi arrived at the model by working it out for that particular robot, and at the gains by tuning on the machine; the general theory of control, planning and learning that would let the same student design rather than rediscover is not something our undergraduate curriculum provides. Yongyi recognises this and has chosen a taught master's for that reason, which I consider the right decision at the right time.

I recommend Yongyi Lai for admission without hesitation, and I would be glad to provide any further information.

Yours sincerely,

Fu Xianghua
Associate Dean, School of Artificial Intelligence
Shenzhen Technology University
fuxianghua@sztu.edu.cn
Telephone: +86 136 3282 1675

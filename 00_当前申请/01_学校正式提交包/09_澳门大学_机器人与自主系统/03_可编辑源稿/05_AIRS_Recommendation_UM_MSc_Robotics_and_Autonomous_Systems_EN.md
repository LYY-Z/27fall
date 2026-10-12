# Recommendation Letter — AIRS Mentor

Shenzhen Institute of Artificial Intelligence and Robotics for Society (AIRS)

Date: 21 September 2026

Dear Members of the Admissions Committee,

I am writing to recommend Yongyi Lai for admission to the MSc in Robotics and Autonomous Systems at the University of Macau.

I am a Robot Development Engineer at the Shenzhen Institute of Artificial Intelligence and Robotics for Society (AIRS), where I supervised Yongyi directly as a robotics software intern from September 2025 to March 2026. During those six months Yongyi was responsible for the chassis balance control of a three-omni-wheel ballbot carrying a dual-arm upper body, a demanding control problem in our group. Under my supervision, Yongyi made steady progress toward this objective.

The task was to keep a dynamically unstable base balanced while two arms moved on top of it, which shifts the centre of mass continuously. Yongyi built the control state from IMU and wheel feedback, designed a cascaded controller in which a position outer loop generates bounded attitude references for an attitude inner loop, allocated the resulting actions to the three wheels through the wheel kinematics, and deployed and tuned the whole loop on the physical robot. To handle the arm disturbance, Yongyi estimated the centre-of-mass offset from the arm joint states using the robot's URDF model with Pinocchio and fed it into the balance controller as gravity feedforward, then verified the effect by comparing the balance response with compensation switched on and off under fixed arm trajectories. By the end of the internship the chassis maintained dynamic balance while both arms executed their trajectories, which was the objective we had set.

What stood out was Yongyi's ability to return to model-based analysis when empirical tuning could no longer fully explain the robot's behaviour. Rather than continuing to adjust gains without a model, Yongyi derived a four-state inverted-pendulum model of the ballbot, linearised it and used LQR to analyse how the weights on position, velocity, tilt and tilt rate trade stability against control effort. That analysis became our reference for interpreting the deployed controller's gains, identifying state anomalies and locating actuator saturation. It also demonstrated analytical ability beyond what I would normally expect from an undergraduate intern.

Yongyi was equally reliable on the engineering safeguards that make a hardware loop trustworthy: ROS state processing and CAN motor execution, state initialisation on re-enable, output limiting, and fall detection and recovery. These safeguards were implemented carefully and documented clearly, allowing the robot to be tested repeatedly under controlled conditions. Yongyi communicated progress and problems concisely, asked precise questions, and worked independently once a direction was agreed.

Yongyi discussed with me the plan to take a taught master's in robotics or AI before working as an algorithm engineer. Given how much of this internship's progress came from Yongyi turning to model-based analysis when tuning ran out, I think that is the right next step. On the evidence of this internship, Yongyi has the technical ability, the hands-on discipline and the intellectual curiosity to benefit fully from your programme. I recommend Yongyi without reservation and would be glad to answer any questions.

Sincerely,

Chen Dansheng
Robot Development Engineer
Shenzhen Institute of Artificial Intelligence and Robotics for Society (AIRS)
chendansheng@cuhk.edu.cn
电话：13651414010

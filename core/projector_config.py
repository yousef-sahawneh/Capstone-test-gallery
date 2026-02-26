class ProjectorConfig:
    # Intrinsics — derived from AAXA P6 Ultimate (throw ratio 1.2, 1280x800)
    width  = 1280
    height = 800
    fx     = 1536.0   # width * throw_ratio
    fy     = 1536.0
    cx     = 640.0    # width / 2
    cy     = 400.0    # height / 2

    # Projector position in world frame (mm), derived from OnShape design.
    # Offset from right IR camera (cam_trans_x=160, cam_trans_y=-50, cam_trans_z=515):
    #   OnShape X=+0.290in (+7.37mm, rightward)  → world +X
    #   OnShape Y=+1.696in (+43.08mm, away)      → world -Y
    #   Z: front face coplanar with camera face  → same world_pos_z as camera
    # ⚠️ Verify sign of world_pos_y — flip to -50 + 43.08 = -6.92 if Y axis is inverted.
    world_pos_x = 167.37
    world_pos_y = -93.08
    world_pos_z = 515.0

    # Color scale: offsets above this value are shown as max red
    max_carve_mm = 30.0

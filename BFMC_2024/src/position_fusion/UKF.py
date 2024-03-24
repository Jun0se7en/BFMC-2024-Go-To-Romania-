import math

import numpy as np
from filterpy.kalman import MerweScaledSigmaPoints
from filterpy.kalman import UnscentedKalmanFilter as UKF
from filterpy.kalman import unscented_transform

# state [x y v heading]
imu_heading = 0.1
imu_acc = 0.1
uwb_std = 0.2


def wrapAngle(Angle):
    # print(Angle)
    Angle = Angle % (2 * np.pi)  # force in range [0, 2 pi)
    if Angle > np.pi:  # move to [-pi, pi)
        Angle -= 2 * np.pi
    return Angle


class UKF_IMU(UKF):
    def __init__(self, dt, WheelBase, alpha, kappa, beta):
        self._dt = dt
        self._WheelBase = WheelBase
        self.points = MerweScaledSigmaPoints(
            n=4,
            alpha=alpha,
            beta=beta,
            kappa=kappa,
            subtract=self.residual_x,
            # sqrt_method=np.linalg.eig,
        )
        self.UT = unscented_transform
        UKF.__init__(
            self,
            dim_x=4,
            dim_z=3,
            dt=dt,
            hx=self.IMU_hx,
            fx=self.IMU_fx,
            points=self.points,
            x_mean_fn=self.state_mean,
            residual_x=self.residual_x,
            residual_z=self.residual_z,
        )
        self.LOW_SPEED_THRESHOLD = 0.01

    def predict(self, dt=None, u=None):
        self._dt = dt
        # calculate sigma points for given mean and covariance
        # self.compute_process_sigmas(dt, self.IMU_fx, **fx_args)
        sigmas = self.points.sigma_points(self.x, self.P)

        for i, s in enumerate(sigmas):
            # 4 state -> 9 sigma points (2n+1)
            self.sigmas_f[i] = self.IMU_fx(s, dt, u)
        # pass sigmas through the unscented transform to compute prior
        self.x, self.P = self.UT(
            self.sigmas_f, self.Wm, self.Wc, self.Q, self.x_mean, self.residual_x
        )

        # save prior
        self.x_prior = np.copy(self.x)
        self.P_prior = np.copy(self.P)

    def IMU_fx(self, x, dt=None, u=None):
        _x, _y, _v, _theta = x[0], x[1], x[2], x[3]
        if u is None:
            _Velo, _alpha = _v, 0
        else:
            _Velo, _alpha = u["speed"], u["steer"]
        _dt = dt
        _wheelbase = self._WheelBase
        # bycicle model : assume IMU is at the center of the car, where
        # _beta : slip angle
        # _vx, _vy : velocity in x and y direction
        # _vtheta : angular velocity
        # _alpha : steering angle
        if _v < self.LOW_SPEED_THRESHOLD:
            # At low speeds, reduce the effect of steering on heading change.
            _beta = 0  # Slip angle effect is minimized.
            _vtheta = 0  # Minimal change in heading due to steering.
        else:
            # Normal operation
            _beta = np.arctan(np.tan(_alpha) / 2)
            _vtheta = (_v / _wheelbase) * np.tan(_alpha) * np.cos(_beta)
        _vx = _v * np.cos(_theta + _beta)
        _vy = _v * np.sin(_theta + _beta)
        x[0] = _x + _vx * _dt
        x[1] = _y + _vy * _dt
        x[2] = _Velo
        x[3] = _theta + _vtheta * _dt
        # print(x, _vx * _dt, _vy * _dt, _dt)
        return x

    def residual_x(self, a, b):
        y = a - b
        # print(y)
        y[3] = wrapAngle(y[3])
        return y

    def residual_z(self, a, b):
        y = a - b
        if len(a) == 1:
            y = wrapAngle(y)
        return y

    def IMU_hx(self, s):
        return np.array([s[3]])

    def UWB_hx(self, s):
        return np.array([s[0], s[1]])

    def update_IMU(self, heading):
        heading_noise = np.array([imu_heading])
        self.update(heading, R=heading_noise, hx=self.IMU_hx)

    def update_UWB(self, z):
        uwb_noise = np.diag([uwb_std**2, uwb_std**2])
        self.update(z, R=uwb_noise, hx=self.UWB_hx)

    def state_mean(self, sigmas, Wm):
        x = np.zeros(4)       
        sum_sin = np.dot(np.sin(sigmas[:, 3]), Wm)
        sum_cos = np.dot(np.cos(sigmas[:, 3]), Wm)
        x[0] = np.dot(sigmas[:, 0], Wm)
        x[1] = np.dot(sigmas[:, 1], Wm)
        x[2] = np.dot(sigmas[:, 2], Wm)
        x[3] = math.atan2(sum_sin, sum_cos)

        return x

import threading
import time
import math
from enum import Enum
from datetime import datetime


class GateState(Enum):
    CLOSED = "关闭"
    OPENING = "开启中"
    OPEN = "已开启"
    CLOSING = "关闭中"


class ParkingGate:
    def __init__(self):
        self.state = GateState.CLOSED
        self.whitelist = [
            "京A12345",
            "沪B67890",
            "粤C11111",
            "浙D22222",
            "苏E33333",
        ]
        self.parked_plates = set()
        self.entry_records = []
        self._timer = None
        self._current_plate = None
        self.blacklist = {}
        self.simulated_hours = {}
        self._parking_timers = {}
        self._timer_running = {}

    def process_plate(self, plate):
        if plate not in self.whitelist:
            print(f"[无效车牌] '{plate}' 不在白名单中，禁止通行。")
            return

        if self.blacklist.get(plate, 0) > 20:
            print(f"\n{'!'*40}")
            print(f"[报警] 车牌 '{plate}' 累计欠费 {self.blacklist[plate]:.2f} 元！")
            print(f"[报警] 已拦截并报警！禁止入场！")
            print(f"{'!'*40}\n")
            return

        if plate in self.parked_plates:
            print(f"[拒绝] 车牌 '{plate}' 已在场内，未出场前不可重复入场。")
            return

        if self.state != GateState.CLOSED:
            print(f"[提示] 道闸当前状态: {self.state.value}，请等待。")
            return

        print(f"[识别成功] 车牌 '{plate}' 验证通过！")
        self._open_gate(plate)

    def _open_gate(self, plate):
        self.state = GateState.OPENING
        print(f"[道闸] 正在抬杆...")
        self.state = GateState.OPEN
        print(f"[道闸] 已抬杆，车辆请通行。")

        self.parked_plates.add(plate)
        self._current_plate = plate
        entry_time = datetime.now()
        self.entry_records.append({"plate": plate, "time": entry_time})
        print(f"[记录] 入场时间: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")

        self.simulated_hours[plate] = 0
        self._timer_running[plate] = True
        self._start_parking_timer(plate)

        self._cancel_timer()
        self._timer = threading.Timer(3.0, self._close_gate_entry)
        self._timer.start()
        print(f"[道闸] 入口3秒后自动关闭...")
        print(f"[计时] 已开始计时（每秒模拟1小时）")

    def _start_parking_timer(self, plate):
        if not self._timer_running.get(plate, False):
            return
        self.simulated_hours[plate] += 1
        hours = self.simulated_hours[plate]
        print(f"\n[计时] {plate} 已停车 {hours} 小时（费用: {hours * 2} 元）")
        print(f"请输入指令: ", end="", flush=True)
        t = threading.Timer(1.0, self._start_parking_timer, args=[plate])
        self._parking_timers[plate] = t
        t.start()

    def _stop_parking_timer(self, plate):
        self._timer_running[plate] = False
        if plate in self._parking_timers:
            timer = self._parking_timers[plate]
            if timer.is_alive():
                timer.cancel()
            del self._parking_timers[plate]

    def exit_plate(self, plate):
        if plate not in self.parked_plates:
            print(f"[错误] 车牌 '{plate}' 不在场内，无法出场。")
            return

        self._stop_parking_timer(plate)

        hours = self.simulated_hours.get(plate, 0)
        if hours < 1:
            hours = 1
        fee = hours * 2

        print(f"\n{'='*40}")
        print(f"[计费] 车牌: {plate}")
        print(f"[计费] 停车时长: {hours} 小时")
        print(f"[计费] 应付费用: {fee:.2f} 元")
        print(f"{'='*40}")

        self._process_payment(plate, fee)

    def _process_payment(self, plate, amount):
        paid = False
        debt_recorded = False
        while not paid:
            print(f"\n请选择支付方式:")
            print(f"  1 - 现金支付")
            print(f"  2 - 扫码支付")
            print(f"  3 - 拒绝支付")

            choice = input("请选择 (1/2/3): ").strip()
            if choice == "1":
                print(f"\n[支付] 正在处理现金支付...")
                time.sleep(1)
                print(f"[支付] 现金支付 {amount:.2f} 元成功！")
                paid = True
            elif choice == "2":
                print(f"\n[支付] 请扫描二维码...")
                print(f"[支付] ████████████████")
                print(f"[支付] ██  扫码付款  ██")
                print(f"[支付] ██ {amount:.2f}元 ██")
                print(f"[支付] ████████████████")
                time.sleep(2)
                print(f"[支付] 扫码支付 {amount:.2f} 元成功！")
                paid = True
            elif choice == "3":
                if not debt_recorded:
                    self.blacklist[plate] = self.blacklist.get(plate, 0) + amount
                    debt_recorded = True
                total_debt = self.blacklist[plate]
                print(f"\n{'!'*40}")
                print(f"[拦截] 道闸保持关闭，禁止抬杆！")
                print(f"[拦截] 未缴费车辆无法离场！")
                print(f"[警告] {plate} 累计欠费: {total_debt:.2f} 元")
                if total_debt > 20:
                    print(f"[报警] 累计欠费超过20元，已加入黑名单！")
                print(f"{'!'*40}")
                print(f"\n[提示] 请完成缴费后道闸方可开启。")
            else:
                print(f"[提示] 无效选择，请输入 1、2 或 3。")

        if plate in self.blacklist:
            del self.blacklist[plate]
            print(f"[结清] {plate} 欠费已清零，黑名单已移除。")
        self._exit_gate(plate)

    def _exit_gate(self, plate):
        print(f"\n[道闸] 出口正在抬杆...")
        time.sleep(0.5)
        print(f"[道闸] 出口已抬杆，车辆请通行。")
        self.parked_plates.discard(plate)
        if plate in self.simulated_hours:
            del self.simulated_hours[plate]
        print(f"[离场] 车牌 '{plate}' 已离场。")
        time.sleep(2)
        print(f"[道闸] 出口已关闭。")

    def _close_gate_entry(self):
        self.state = GateState.CLOSING
        print(f"\n[道闸] 入口正在落杆...")
        self.state = GateState.CLOSED
        self._current_plate = None
        print(f"[道闸] 入口已关闭，等待下一辆车。")
        print(f"请输入指令: ", end="", flush=True)

    def _cancel_timer(self):
        if self._timer and self._timer.is_alive():
            self._timer.cancel()
            self._timer = None

    def shutdown(self):
        self._cancel_timer()
        for plate in list(self._parking_timers.keys()):
            self._stop_parking_timer(plate)


def main():
    gate = ParkingGate()

    print("=" * 40)
    print("      停车场道闸管理系统")
    print("=" * 40)
    print(f"白名单车牌: {gate.whitelist}")
    print("-" * 40)
    print("指令说明:")
    print("  输入车牌号     → 入场")
    print("  exit 车牌号    → 出场缴费")
    print("  q              → 退出系统")
    print("-" * 40)

    try:
        while True:
            cmd = input("请输入指令: ").strip()
            if cmd.lower() == "q":
                print("系统关闭。")
                break
            if not cmd:
                continue

            if cmd.lower().startswith("exit "):
                plate = cmd[5:].strip()
                if plate:
                    gate.exit_plate(plate)
                else:
                    print("[提示] 请输入要出场的车牌号，格式: exit 车牌号")
            else:
                gate.process_plate(cmd)
    except KeyboardInterrupt:
        print("\n系统关闭。")
    finally:
        gate.shutdown()
        if gate.entry_records:
            print(f"\n{'='*40}")
            print("--- 入场记录 ---")
            for record in gate.entry_records:
                print(f"  {record['plate']}  {record['time'].strftime('%Y-%m-%d %H:%M:%S')}")
        if gate.blacklist:
            print(f"\n--- 黑名单 ---")
            for plate, debt in gate.blacklist.items():
                status = "（已拦截）" if debt > 20 else ""
                print(f"  {plate}  欠费: {debt:.2f} 元 {status}")


if __name__ == "__main__":
    main()

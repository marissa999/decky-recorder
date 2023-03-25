import {
	ServerAPI,
	Router
} from "decky-frontend-lib";

export class DeckyRecorderLogic {
	
	serverAPI: ServerAPI;
	pressedAt: number = Date.now();

	constructor(serverAPI: ServerAPI) {
		this.serverAPI = serverAPI;
	}

	notify = async (message: string, duration: number = 1000, body: string = "") => {
		if (!body) {
			body = message;
		}
		await this.serverAPI.toaster.toast({
			title: message,
			body: body,
			duration: duration,
			critical: true
		});
	}

	saveRollingRecording = async  (duration: number) => {
		const res = await this.serverAPI.callPluginMethod('save_rolling_recording', { clip_duration: duration });
		let r = (res.result as number)
		if (r > 0) {
			await this.notify("Saved clip");
		} else if (r == 0) {
			await this.notify("Too early to record another clip");
		} else {
			await this.notify("ERROR: Could not save clip");
		}
	}

	toggleRolling = async (isRolling: boolean) => {
		if (!isRolling) {
			await this.serverAPI.callPluginMethod('enable_rolling', {});
		} else {
			await this.serverAPI.callPluginMethod('disable_rolling', {});
		}
	}

	handleButtonInput = async (val: any[]) => {
		/*
		R2 0
		L2 1
		R1 2
		R2 3
		Y  4
		B  5
		X  6
		A  7
		UP 8
		Right 9
		Left 10
		Down 11
		Select 12
		Steam 13
		Start 14
		QAM  ???
		L5 15
		R5 16*/
		for (const inputs of val) {
			if (Date.now() - this.pressedAt < 2000) {
				continue;
			}
			if (inputs.ulButtons && inputs.ulButtons & (1 << 13) && inputs.ulButtons & (1 << 14)) {
				this.pressedAt = Date.now();
				(Router as any).DisableHomeAndQuickAccessButtons();
				setTimeout(() => {
					(Router as any).EnableHomeAndQuickAccessButtons();
				}, 1000)
				const isRolling = await this.serverAPI.callPluginMethod("is_rolling", {});
				if (isRolling.result as boolean) {
					await this.saveRollingRecording(30);
				} else {
					await this.notify("Enabling replay mode", 1500, "Steam + Start to save last 30 seconds");
					this.toggleRolling(false);
				}
			}
		}
	}

}
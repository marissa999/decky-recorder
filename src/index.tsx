import {
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses,
	Dropdown,
	DropdownOption,
	SingleDropdownOption
} from "decky-frontend-lib";

import {
	VFC,
	useState,
	useEffect
} from "react";

import { GeneralSettings } from "./GeneralSettings";
import { LocalFileMode } from "./Modes/LocalFileMode";
import { ReplayMode } from "./Modes/ReplayMode";
import { DeckyRecorderLogic } from "./DeckyRecorderLogic";

import { FaVideo } from "react-icons/fa";

const DeckyRecorder: VFC<{
	serverAPI: ServerAPI,
	logic: DeckyRecorderLogic
}> = ({ serverAPI, logic }) => {

	const localRecordingMode = { data: "localFile" as string, label: "Local Recording" } as SingleDropdownOption
	const replayMode = { data: "replayMode" as string, label: "Replay Mode" } as SingleDropdownOption
	const modeOptions: DropdownOption[] = [localRecordingMode, replayMode];
	const [mode, setMode] = useState<DropdownOption>(localRecordingMode);

	const [isCapturing, setCapturing] = useState<boolean>(false);
	const [isRolling, setRolling] = useState<boolean>(false);	

	const initState = async () => {

		const getModeResponse = await serverAPI.callPluginMethod('get_current_mode', {});
		if (getModeResponse.result as string == "localFile") {
			setMode(localRecordingMode);
		} else if (getModeResponse.result as string == "replayMode") {
			setMode(replayMode);
		} else {
			setMode(localRecordingMode);
		}

		const getIsCapturingResponse = await serverAPI.callPluginMethod('is_capturing', {});
		setCapturing(getIsCapturingResponse.result as boolean);

		const getIsRollingResponse = await serverAPI.callPluginMethod('is_rolling', {});
		setRolling(getIsRollingResponse.result as boolean);

	}

	const disableSettings = () => {
		if (isCapturing) {
			return true;
		}
		if (isRolling) {
			return true;
		}
		return false;
	}

	useEffect(() => {
		initState();
	}, []);

	return (
		<PanelSection>

			<PanelSectionRow>
				<div>Mode</div>
				<Dropdown
					menuLabel="Select the mode you want to use"
					disabled={disableSettings()}
					strDefaultLabel={mode.label as string}
					rgOptions={modeOptions}
					selectedOption={mode}
					onChange={(newMode) => {
						serverAPI.callPluginMethod('set_current_mode', { mode: newMode.data });
						setMode(newMode);
					}}
				/>
			</PanelSectionRow>

			{(mode.data == localRecordingMode.data)
				? <LocalFileMode serverAPI={serverAPI} isCapturing={isCapturing} setCapturing={setCapturing} /> : null}

			{(mode.data == replayMode.data)
				? <ReplayMode serverAPI={serverAPI} isRolling={isRolling} setRolling={setRolling} logic={logic} /> : null}

			<GeneralSettings serverAPI={serverAPI} isRunning={disableSettings()} />

		</PanelSection>
	);

};


export default definePlugin((serverApi: ServerAPI) => {
	let logic = new DeckyRecorderLogic(serverApi);
	let input_register = window.SteamClient.Input.RegisterForControllerStateChanges(logic.handleButtonInput);
	return {
		title: <div className={staticClasses.Title}>Decky Recorder</div>,
		content: <DeckyRecorder serverAPI={serverApi} logic={logic} />,
		icon: <FaVideo />,
		onDismount() {
			input_register.unregister();
		},
		alwaysRender: true
	};
});
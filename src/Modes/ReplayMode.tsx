import {
	PanelSectionRow,
	ServerAPI,
	ButtonItem,
	ToggleField,
	SingleDropdownOption,
	DropdownOption,
	Dropdown
} from "decky-frontend-lib";

import {
	VFC,
	useState,
	useEffect
} from "react";

import { DeckyRecorderLogic } from "../DeckyRecorderLogic";

export const ReplayMode: VFC<{ 
	serverAPI: ServerAPI, 
	isReplayMode: boolean
	setReplayMode: React.Dispatch<React.SetStateAction<boolean>>, 
	logic: DeckyRecorderLogic
}> = ({serverAPI, isReplayMode, setReplayMode, logic}) => {

	const [isReplayModeAutoStart, setReplayModeAutoStart] = useState<boolean>(false);	
 
	const bufferOption30 = { data: 30 as number, label: "30 Seconds" } as SingleDropdownOption
	const bufferOption60 = { data: 60 as number, label: "1 Minute" } as SingleDropdownOption;
	const bufferOption120 = { data: 120 as number, label: "2 Minutes" } as SingleDropdownOption;
	const bufferOption300 = { data: 300 as number, label: "5 Minutes" } as SingleDropdownOption;
	const bufferOptions: DropdownOption[] = [
		bufferOption30,
		bufferOption60,
		bufferOption120,
		bufferOption300,
	];
	const [buffer, setBuffer] = useState<DropdownOption>(bufferOption30);

	const initState = async () => {
		
		const getLocalBufferLengthResponse = await serverAPI.callPluginMethod('get_buffer_length', {})
		const localBufferLengthNumber: number = getLocalBufferLengthResponse.result as number;
		if (localBufferLengthNumber == 30) {
			setBuffer(bufferOption30)
		} else if (localBufferLengthNumber == 60) {
			setBuffer(bufferOption60)
		} else if (localBufferLengthNumber == 120) {
			setBuffer(bufferOption120)
		} else if (localBufferLengthNumber == 300) {
			setBuffer(bufferOption120)
		} else {
			// should never happen? default back to 30
			setBuffer(bufferOption30)
		}

		const getReplayModeAutostartResponse = await serverAPI.callPluginMethod('get_replaymode_autostart', {})
		setReplayModeAutoStart(getReplayModeAutostartResponse.result as boolean)

	}

	useEffect(() => {
		initState();
	}, []);

	const replayModeButtonPressed = async () => {
		if (!isReplayMode) {
			serverAPI.callPluginMethod('enable_replaymode', {});
			setReplayMode(true);
		} else {
			serverAPI.callPluginMethod('disable_replaymode', {});
			setReplayMode(false);
		}
	}

	const saveReplay = async () => {
		logic.saveRollingRecording(buffer.data as number)
	}

	const replayModeButtonText = (): string => {
		if (isReplayMode === false) {
			return "Start Replay Recording";
		} else {
			return "Stop Replay Recording";
		}
	}

	return (
		<PanelSectionRow>
			<ButtonItem
				bottomSeparator="none"
				layout="below"
				onClick={() => {replayModeButtonPressed()}}>
				{replayModeButtonText()}
			</ButtonItem>
			<ButtonItem
				bottomSeparator="none"
				disabled={!isReplayMode}
				layout="below"
				onClick={() => {saveReplay()}}>
				Save replay
			</ButtonItem>
			<Dropdown
				menuLabel="Select the buffer length"
				disabled={isReplayMode}
				strDefaultLabel={"Length: " + buffer.label as string}
				rgOptions={bufferOptions}
				selectedOption={buffer}
				onChange={(newBufferLength) => {
					serverAPI.callPluginMethod('set_buffer_length', { bufferLength: newBufferLength.data });
					setBuffer(newBufferLength);}}
			/>
			<ToggleField
					label="Auto Enable at Start"
					checked={isReplayModeAutoStart}
					onChange={(e) => { 
						serverAPI.callPluginMethod('set_replaymode_autostart', { replaymode_autostart: e });
						setReplayModeAutoStart(e);}} />
			<div>Steam + Start saves a 30 second clip in replay mode. If replay mode is off, this shortcut will enable it.</div>
		</PanelSectionRow>
	);

};
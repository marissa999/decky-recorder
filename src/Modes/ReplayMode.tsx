import {
	PanelSectionRow,
	ServerAPI,
	ButtonItem,
	ToggleField,
	Router,
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
	isRolling: boolean
	setRolling: React.Dispatch<React.SetStateAction<boolean>>, 
	logic: DeckyRecorderLogic
}> = ({serverAPI, isRolling, setRolling, logic}) => {

	const [isRollingAutoStart, setRollingAutoStart] = useState<boolean>(false);	
 
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

	}

	useEffect(() => {
		initState();
	}, []);

	const replayModeButtonPressed = async () => {
		if (isRolling === false) {
			setRolling(true);
			Router.CloseSideMenus();
		} else {
			setRolling(false);
		}
	}

	const replayModeButtonText = (): string => {
		if (isRolling === false) {
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
			<Dropdown
				menuLabel="Select the video file format"
				disabled={isRolling}
				strDefaultLabel={"Length: " + buffer.label as string}
				rgOptions={bufferOptions}
				selectedOption={buffer}
				onChange={(newBufferLength) => {
					serverAPI.callPluginMethod('set_buffer_length', { bufferLength: newBufferLength.data });
					setBuffer(newBufferLength);
				}}
			/>
			<ToggleField
					label="Auto Enable at Start"
					checked={isRollingAutoStart}
					onChange={(e) => { setRollingAutoStart(e)}} />
			<div>Steam + Start saves a 30 second clip in replay mode. If replay mode is off, this shortcut will enable it.</div>
		</PanelSectionRow>
	);

};
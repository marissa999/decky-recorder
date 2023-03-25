import {
	PanelSectionRow,
	ServerAPI,
	ButtonItem,
	ToggleField,
	Router
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
 
	const initState = async () => {
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
			<ToggleField
					label="Auto Enable at Start"
					checked={isRollingAutoStart}
					onChange={(e) => { setRollingAutoStart(e)}}
				/>
			<div>Steam + Start saves a 30 second clip in replay mode. If replay mode is off, this shortcut will enable it.</div>
		</PanelSectionRow>
	);

};
import {
	ButtonItem,
	PanelSectionRow,
	ServerAPI,
	Router,
} from "decky-frontend-lib";

import {
	VFC
} from "react";

export const LocalFileMode: VFC<{
	serverAPI: ServerAPI,
	isCapturing: boolean,
	setCapturing: React.Dispatch<React.SetStateAction<boolean>>
}> = ({serverAPI, isCapturing, setCapturing}) => {

	const recordingButtonPress = async () => {
		if (isCapturing === false) {
			setCapturing(true);
			await serverAPI.callPluginMethod('start_capturing', {});
			Router.CloseSideMenus();
		} else {
			setCapturing(false);
			await serverAPI.callPluginMethod('stop_capturing', {});
		}
	}

	const getRecordingButtonText = (): string => {
		if (isCapturing === false) {
			return "Start Recording";
		} else {
			return "Stop Recording";
		}
	}

	return (
		<PanelSectionRow>
			<ButtonItem
				bottomSeparator="none"
				layout="below"
				onClick={() => {recordingButtonPress()}}>
				{getRecordingButtonText()}
			</ButtonItem>
		</PanelSectionRow>
	);

};
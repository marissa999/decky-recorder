import {
	ButtonItem,
	PanelSectionRow,
	ServerAPI,
	Router,
} from "decky-frontend-lib";

import {
	VFC,
	useState,
	useEffect
} from "react";

export const LocalFileMode: VFC<{ serverAPI: ServerAPI}> = ({serverAPI}) => {

	const [isCapturing, setCapturing] = useState<boolean>(false);

	const initState = async () => {
		const getIsCapturingResponse = await serverAPI.callPluginMethod('is_capturing', {});
		setCapturing(getIsCapturingResponse.result as boolean);
	}

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

	useEffect(() => {
		initState();
	}, []);

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
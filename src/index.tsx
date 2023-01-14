import {
	ButtonItem,
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses,
	Router
} from "decky-frontend-lib";

import {
	VFC, 
	useState,
	useEffect
} from "react";

import { FaVideo } from "react-icons/fa";

const DeckyRecorder: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {

	const [recordingStarted, setRecordingStarted] = useState(false);

	const initState = async () => {
		const is_recording_response = await serverAPI.callPluginMethod('is_recording', {})
		setRecordingStarted(is_recording_response.result as boolean);
	}

	const recordingButtonPress = async() => {
		if (recordingStarted === false){
			setRecordingStarted(true);
			await serverAPI.callPluginMethod('start_recording', {});
		} else {
			setRecordingStarted(false);
			await serverAPI.callPluginMethod('end_recording', {});
		}
	}

	useEffect(() => {
		initState();
	  }, []);

	return (
	<PanelSection>
		<PanelSectionRow>
			<ButtonItem 
				label="Recordings will be saved to ~/Videos"
				layout="below"
				onClick={() => {
					recordingButtonPress();
					Router.CloseSideMenus();
				}}>
				{recordingStarted === false ? "Start Recording" : "Stop Recording"}
			</ButtonItem>
		</PanelSectionRow>
	</PanelSection>
	);
};

export default definePlugin((serverApi: ServerAPI) => {
	return {
		title: <div className={staticClasses.Title}>Decky Recorder</div>,
		content: <DeckyRecorder serverAPI={serverApi} />,
		icon: <FaVideo />,
	};
});
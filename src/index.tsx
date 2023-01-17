import {
	ButtonItem,
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses,
	ToggleField,
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
	const [microphone, setMicrophone] = useState(false);

	const initState = async () => {
		const is_recording_response = await serverAPI.callPluginMethod('is_recording', {})
		setRecordingStarted(is_recording_response.result as boolean);

		const microphone_response = await serverAPI.callPluginMethod('get_mic', {})
		setMicrophone(microphone_response.result as boolean);

	}

	const recordingButtonPress = async() => {
		if (recordingStarted === false){
			setRecordingStarted(true);
			await serverAPI.callPluginMethod('start_recording', {});
			Router.CloseSideMenus();
		} else {
			setRecordingStarted(false);
			await serverAPI.callPluginMethod('end_recording', {});
		}
	}

	const getLabelText = (): string => {
		return "Recordings will be saved to ~/Videos";
	}

	const getButtonText = (): string => {
		if (recordingStarted === false){
			return "Start Recording";
		} else {
			return "Stop Recording";
		}
	}

	useEffect(() => {
		initState();
	}, []);

	return (
		<PanelSection>
			<PanelSectionRow>
				<ButtonItem
					label={getLabelText()}
					bottomSeparator="none"
					layout="below"
					onClick={() => {
						recordingButtonPress();
					}}>
					{getButtonText()}
				</ButtonItem>
			</PanelSectionRow>
			<PanelSectionRow>
				<ToggleField
					disabled={recordingStarted === true}
					label="Record Microphone"
					bottomSeparator="none"
					checked={microphone === true}
					onChange={(newValue: boolean) => {
						serverAPI.callPluginMethod('set_mic', {mic: newValue});
						setMicrophone(newValue);
					}}
				/>
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
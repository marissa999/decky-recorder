import {
	ButtonItem,
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses,
	Dropdown,
	DropdownOption,
	SingleDropdownOption,
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

	const [ip, setIp] = useState("127.0.0.1");

	const modeOptionLocalFile = {data: "localFile", label: "Local File"} as SingleDropdownOption
	const modeOptionRtsp = {data: "rtsp", label: "RTSP-Server (OBS)"} as SingleDropdownOption;
	const modeOptions: DropdownOption[] = [modeOptionLocalFile, modeOptionRtsp];
	const [currentMode, setCurrentMode] = useState(modeOptionLocalFile);

	const initState = async () => {
		const is_recording_response = await serverAPI.callPluginMethod('is_recording', {})
		setRecordingStarted(is_recording_response.result as boolean);

		const ip_response = await serverAPI.callPluginMethod('wlan_ip', {})
		setIp(ip_response.result as string);

		const currentModeResponse = await serverAPI.callPluginMethod('current_mode', {})
		const currentModeResponseString = currentModeResponse.result as string;
		if (currentModeResponseString == modeOptionLocalFile.data){
			setCurrentMode(modeOptionLocalFile)
		} else if (currentModeResponseString == modeOptionRtsp.data){
			setCurrentMode(modeOptionRtsp)
		}
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

	const strDefaultLabelText = (): string => {
		if (currentMode !== null){
			return currentMode.label as string
		}
		return "Select a mode";
	}

	const getLabelText = (): string => {
		if (currentMode.data === modeOptionLocalFile.data){
			return "Recordings will be saved to ~/Videos";
		} else if (currentMode.data === modeOptionRtsp.data){
			return "RTSP Stream will listen on " + ip + ":5000";
		}
		return "error?" + currentMode.data
	}

	const getButtonText = (): string => {
		if (recordingStarted === false){
			if (currentMode.data === modeOptionLocalFile.data){
				return "Start Recording";
			} else if (currentMode.data === modeOptionRtsp.data){
				return "Start Streaming";
			}
		} else {
			if (currentMode.data === modeOptionLocalFile.data){
				return "Stop Recording";
			} else if (currentMode.data === modeOptionRtsp.data){
				return "Stop Streaming";
			}
		}
		return "Unknown state, please restart"
	}

	useEffect(() => {
		initState();
	}, []);

	return (
	<PanelSection>
		<PanelSectionRow>
			<ButtonItem 
				label={getLabelText()}
				layout="below"
				onClick={() => {
					recordingButtonPress();
				}}>
				{getButtonText()}
			</ButtonItem>
		</PanelSectionRow>
		<PanelSectionRow>
			<Dropdown
				disabled={recordingStarted === true}
				menuLabel="Select the mode you want use"
				strDefaultLabel={strDefaultLabelText()}
				rgOptions={modeOptions}
				selectedOption={currentMode}
				onChange={(newMode) => {
					serverAPI.callPluginMethod('set_current_mode', {mode: newMode.data});
					setCurrentMode(newMode);
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
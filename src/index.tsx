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
	const [deckaudio, setDeckaudio] = useState(true);
	const [microphone, setMicrophone] = useState(false);
	const [ip, setIp] = useState("127.0.0.1");

	const modeOptionLocalFile = {data: "localFile", label: "Local File"} as SingleDropdownOption
	const modeOptionRtsp = {data: "rtsp", label: "Host RTSP-Server"} as SingleDropdownOption;
	const modeOptions: DropdownOption[] = [modeOptionLocalFile, modeOptionRtsp];
	const [currentMode, setCurrentMode] = useState(modeOptionLocalFile);

	const initState = async () => {
		const is_recording_response = await serverAPI.callPluginMethod('is_recording', {})
		setRecordingStarted(is_recording_response.result as boolean);

		const ip_response = await serverAPI.callPluginMethod('get_wlan_ip', {})
		setIp(ip_response.result as string);

		const deckaudio_response = await serverAPI.callPluginMethod('get_deckaudio', {})
		setDeckaudio(deckaudio_response.result as boolean);

		const microphone_response = await serverAPI.callPluginMethod('get_mic', {})
		setMicrophone(microphone_response.result as boolean);

		const currentModeResponse = await serverAPI.callPluginMethod('get_current_mode', {})
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
			return "RTSP-Server will listen on " + ip + ":5000";
		}
		return ""
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
					label="Record Deck Audio"
					bottomSeparator="none"
					checked={deckaudio === true}
					onChange={(newValue: boolean) => {
						serverAPI.callPluginMethod('set_deckaudio', {deckaudio: newValue});
						setDeckaudio(newValue);
					}}
				/>
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
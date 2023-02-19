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

	const [isCapturing, setCapturing] = useState<boolean>(false);
	const [mode, setMode] = useState<string>("localFile");
	const [audioBitrate, setAudioBitrate] = useState<number>(128);
	const [localFilePath, setLocalFilePath] = useState<string>("/home/deck/Videos");
	const [localFileFormat, setLocalFileFormat] = useState<string>("mp4");

	const initState = async () => {
		const getIsCapturingResponse = await serverAPI.callPluginMethod('is_capturing', {})
		setCapturing(getIsCapturingResponse.result as boolean);

		const getModeResponse = await serverAPI.callPluginMethod('get_current_mode', {})
		setMode(getModeResponse.result as string);

		const getAudioBitrateResponse = await serverAPI.callPluginMethod('get_audio_bitrate', {})
		setAudioBitrate(getAudioBitrateResponse.result as number);

		const getLocalFilepathResponse = await serverAPI.callPluginMethod('get_local_filepath', {})
		setLocalFilePath(getLocalFilepathResponse.result as string);

		const getLocalFileFormatResponse = await serverAPI.callPluginMethod('get_local_fileformat', {})
		setLocalFileFormat(getLocalFileFormatResponse.result as string);
	}

	const recordingButtonPress = async() => {
		if (isCapturing === false){
			setCapturing(true);
			await serverAPI.callPluginMethod('start_capturing', {});
			Router.CloseSideMenus();
		} else {
			setCapturing(false);
			await serverAPI.callPluginMethod('stop_capturing', {});
		}
	}

	const getLabelText = (): string => {
		return "Recordings will be saved to " + localFilePath;
	}

	const getButtonText = (): string => {
		if (isCapturing === false){
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
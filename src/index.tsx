import {
	ButtonItem,
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses,
	Dropdown,
	DropdownOption,
	Router
} from "decky-frontend-lib";

import {
	VFC, 
	useState,
} from "react";

import { FaVideo } from "react-icons/fa";

const DeckyRecorder: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {

	const [isRecording, setRecording] = useState<boolean>(false);

	const [mode, setMode] = useState<string>("localFile");

	const audioBitrateOption128 = {data: "128", label: "128 Kbps"} as DropdownOption
	const audioBitrateOption192 = {data: "192", label: "192 Kbps"} as DropdownOption
	const audioBitrateOption256 = {data: "256", label: "256 Kbps"} as DropdownOption
	const audioBitrateOption320 = {data: "320", label: "320 Kbps"} as DropdownOption
	const audioBitrateOptions: DropdownOption[] = [audioBitrateOption128, 
		audioBitrateOption192, audioBitrateOption256, audioBitrateOption320];
	const [audioBitrate, setAudioBitrate] = useState<DropdownOption>(audioBitrateOption128);

	const [localFilePath, setLocalFilePath] = useState<string>("/home/deck/Videos");

	const formatOptionMp4 = {data: "mp4", label: "MP4"} as DropdownOption
	const formatOptionMkv = {data: "mkv", label: "Matroska (.mkv)"} as DropdownOption;
	const formatOptionMov = {data: "mov", label: "QuickTime (.mov)"} as DropdownOption;
	const formatOptions: DropdownOption[] = [formatOptionMp4, formatOptionMkv, formatOptionMov];
	const [localFileFormat, setLocalFileFormat] = useState<DropdownOption>(formatOptionMp4);

	const recordingButtonPress = async() => {
		if (isRecording === false){
			setRecording(true);
			await serverAPI.callPluginMethod('start_recording', {
				"mode": mode, 
				"localFilePath": localFilePath,
				"fileformat": localFileFormat.data
			});
			Router.CloseSideMenus();
		} else {
			setRecording(false);
			await serverAPI.callPluginMethod('stop_recording', {});
		}
	}

	const getLabelText = (): string => {
		return "Recordings will be saved to " + localFilePath;
	}

	const getButtonText = (): string => {
		if (isRecording === false){
			return "Start Recording";
		} else {
			return "Stop Recording";
		}
	}

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
				<Dropdown
					disabled={isRecording}
					menuLabel="Select the video file format"
					strDefaultLabel={localFileFormat.label as string}
					rgOptions={formatOptions}
					selectedOption={localFileFormat}
					onChange={(newLocalFileFormat) => {
						setLocalFileFormat(newLocalFileFormat);
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
		alwaysRender: true,
		onDismount() {
			serverApi.callPluginMethod('stop_recording', {});
		},
	};
});
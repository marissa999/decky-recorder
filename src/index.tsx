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
	Router,
        ToggleField
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

	const [isRolling, setRolling] = useState<boolean>(false);

	const audioBitrateOption128 = {data: "128", label: "128 Kbps"} as SingleDropdownOption
	const audioBitrateOption192 = {data: "192", label: "192 Kbps"} as SingleDropdownOption
	const audioBitrateOption256 = {data: "256", label: "256 Kbps"} as SingleDropdownOption
	const audioBitrateOption320 = {data: "320", label: "320 Kbps"} as SingleDropdownOption
	const audioBitrateOptions: DropdownOption[] = [audioBitrateOption128, 
		audioBitrateOption192, audioBitrateOption256, audioBitrateOption320];
	const [audioBitrate, setAudioBitrate] = useState<DropdownOption>(audioBitrateOption128);

	const [localFilePath, setLocalFilePath] = useState<string>("/home/deck/Videos");

	const formatOptionMp4 = {data: "mp4", label: "MP4"} as SingleDropdownOption
	const formatOptionMkv = {data: "mkv", label: "Matroska (.mkv)"} as SingleDropdownOption;
	const formatOptionMov = {data: "mov", label: "QuickTime (.mov)"} as SingleDropdownOption;
	const formatOptions: DropdownOption[] = [formatOptionMp4, formatOptionMkv, formatOptionMov];
	const [localFileFormat, setLocalFileFormat] = useState<DropdownOption>(formatOptionMp4);

	const initState = async () => {
		const getIsCapturingResponse = await serverAPI.callPluginMethod('is_capturing', {});
		setCapturing(getIsCapturingResponse.result as boolean);

		const getIsRollingResponse = await serverAPI.callPluginMethod('is_rolling', {});
		setRolling(getIsRollingResponse.result as boolean);

		const getModeResponse = await serverAPI.callPluginMethod('get_current_mode', {});
		setMode(getModeResponse.result as string);

		const getAudioBitrateResponse = await serverAPI.callPluginMethod('get_audio_bitrate', {});
		const audioBitrateResponseNumber: number = getAudioBitrateResponse.result as number;
		switch (audioBitrateResponseNumber) {
			case 128:
				setAudioBitrate(audioBitrateOption128);
				break;
			case 192:
				setAudioBitrate(audioBitrateOption192)
				break;
			case 256:
				setAudioBitrate(audioBitrateOption256)
				break;
			case 320:
				setAudioBitrate(audioBitrateOption320)
				break;
			default:
				setAudioBitrate(audioBitrateOption128)
				break;
		} 
		
		const getLocalFilepathResponse = await serverAPI.callPluginMethod('get_local_filepath', {})
		setLocalFilePath(getLocalFilepathResponse.result as string);

		const getLocalFileFormatResponse = await serverAPI.callPluginMethod('get_local_fileformat', {})
		const localFileFormatResponseString: string = getLocalFileFormatResponse.result as string;
		if (localFileFormatResponseString == "mp4") {
			setLocalFileFormat(formatOptionMp4)
		} else if (localFileFormatResponseString == "mkv") {
			setLocalFileFormat(formatOptionMkv)
		} else if (localFileFormatResponseString == "mov") {
			setLocalFileFormat(formatOptionMov)
		} else {
			// should never happen? default back to mp4
			setLocalFileFormat(formatOptionMp4)
		}

	}

        const notify(message: string, duration: number = 1000) = async() => {
            await serverAPI.toaster.toast({
            title: message,
            body: message,
            duration: duration,
            critical: true
            });
            setCapturing(true);
        }

	const recordingButtonPress = async() => {
		if (isCapturing === false){
			await serverAPI.callPluginMethod('start_capturing', {});
			Router.CloseSideMenus();
                } else {
			setCapturing(false);
			await serverAPI.callPluginMethod('stop_capturing', {});
		}
	}

        const rollingRecordButtonPress = async(duration: number) => {
            await serverAPI.callPluginMethod('save_rolling_recording', {clip_duration: duration});
            notify("Saved " + number + " second recording");
        }

	const rollingToggled = async () => {
		if (isRolling === false) {
			setRolling(true);
			await serverAPI.callPluginMethod('enable_rolling', {});
		} else {
			setRolling(false);
			await serverAPI.callPluginMethod('disable_rolling', {});
		}
	}

	const getLabelText = (): string => {
		return "Recordings will be saved to " + localFilePath;
	}

	const getRecordingButtonText = (): string => {
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
                            <ToggleField
                            label="Replay Mode"
                            checked={isRolling}
                            onChange={(e)=>{setRolling(e); rollingToggled();}}
                            />
                            <ButtonItem
                                    label={getLabelText()}
                                    bottomSeparator="none"
                                    layout="below"
                                    onClick={() => {
                                            recordingButtonPress();
                                    }}>
                                    {getRecordingButtonText()}
                            </ButtonItem>
                        </PanelSectionRow>

                        <PanelSectionRow>
                                <Dropdown
                                        menuLabel="Select the video file format"
                                        strDefaultLabel={localFileFormat.label as string}
                                        rgOptions={formatOptions}
                                        selectedOption={localFileFormat}
                                        onChange={(newLocalFileFormat) => {
                                                serverAPI.callPluginMethod('set_local_fileformat', {fileformat: newLocalFileFormat.data});
                                                setLocalFileFormat(newLocalFileFormat);
                                        }}
                                />
                        </PanelSectionRow>

                        {(isRolling)
                        ? <PanelSectionRow><ButtonItem disabled={!isCapturing} onClick={() => {rollingRecordButtonPress(30)}}>30 sec</ButtonItem></PanelSectionRow> : null }

                        {(isRolling)
                        ? <PanelSectionRow><ButtonItem disabled={!isCapturing} onClick={() => {rollingRecordButtonPress(60)}}>1 min</ButtonItem></PanelSectionRow> : null }

                        {(isRolling)
                        ? <PanelSectionRow><ButtonItem disabled={!isCapturing} onClick={() => {rollingRecordButtonPress(60*2)}}>2 min</ButtonItem></PanelSectionRow> : null }

                        {(isRolling)
                        ? <PanelSectionRow><ButtonItem disabled={!isCapturing} onClick={() => {rollingRecordButtonPress(60*5)}}>5 min</ButtonItem></PanelSectionRow> : null }

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
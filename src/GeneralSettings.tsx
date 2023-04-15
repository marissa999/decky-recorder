import {
	ButtonItem,
	PanelSectionRow,
	ServerAPI,
	Dropdown,
	DropdownOption,
	SingleDropdownOption
} from "decky-frontend-lib";

import {
	VFC,
	useState,
	useEffect
} from "react";

export const GeneralSettings: VFC<{ 
	serverAPI: ServerAPI
	isRunning: boolean
}> = ({serverAPI, isRunning}) => {

	const [localFilePath, setLocalFilePath] = useState<string>("/home/deck/Videos");

	const formatOptionMp4 = { data: "mp4", label: "MP4" } as SingleDropdownOption
	const formatOptionMkv = { data: "mkv", label: "Matroska (.mkv)" } as SingleDropdownOption;
	const formatOptionMov = { data: "mov", label: "QuickTime (.mov)" } as SingleDropdownOption;
	const formatOptions: DropdownOption[] = [formatOptionMkv, formatOptionMp4, formatOptionMov];
	const [localFileFormat, setLocalFileFormat] = useState<DropdownOption>(formatOptionMp4);

	const initState = async () => {

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

	const pickFolder = async () => {
		const filePickerResponse = await serverAPI.openFilePicker(localFilePath, false);
		setLocalFilePath(filePickerResponse.path)
		await serverAPI.callPluginMethod('set_local_filepath', {localFilePath: filePickerResponse.path});
	}

	const disableFileformatDropdown = () => {
		if (isRunning) {
			return true;
		}
		if (isRunning) {
			return true;
		}
		return false;
	}

	useEffect(() => {
		initState();
	}, []);

	return (
		<PanelSectionRow>

			<ButtonItem
				disabled={disableFileformatDropdown()}
				bottomSeparator="none"
				layout="below"
				onClick={() => {
					pickFolder();
				}}>
				{"Path: " + localFilePath as string}
			</ButtonItem>

			<Dropdown
				menuLabel="Select the video file format"
				disabled={disableFileformatDropdown()}
				strDefaultLabel={"Format: " + localFileFormat.label as string}
				rgOptions={formatOptions}
				selectedOption={localFileFormat}
				onChange={(newLocalFileFormat) => {
					serverAPI.callPluginMethod('set_local_fileformat', { fileformat: newLocalFileFormat.data });
					setLocalFileFormat(newLocalFileFormat);
				}}
			/>

		</PanelSectionRow>
	);

};
import {
	ButtonItem,
	definePlugin,
	PanelSection,
	PanelSectionRow,
	ServerAPI,
	staticClasses
} from "decky-frontend-lib";

import {
	VFC, 
	useState,
	useEffect
} from "react";

import { FaVideo } from "react-icons/fa";

const DeckyRecorder: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {

	const [recordingStarted, setRecordingStarted] = useState(false);
	const [dependenciesInstalled, setDependenciesInstalled] = useState(false);

	const initState = async () => {
		const is_recording_response = await serverAPI.callPluginMethod('is_recording', {})
		setRecordingStarted(is_recording_response.result as boolean);
		const is_deps_installed_response = await serverAPI.callPluginMethod('check_if_deps_installed', {})
		setDependenciesInstalled(is_deps_installed_response.result as boolean);
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

	const installDependencies = async() => {
		await serverAPI.callPluginMethod('install_deps', {});
		setDependenciesInstalled(true);
	}

	const uninstallDependencies = async() => {
		await serverAPI.callPluginMethod('uninstall_deps', {});
		setDependenciesInstalled(false);
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
				disabled={!dependenciesInstalled}
				onClick={() => {
					recordingButtonPress();
				}}>
				{recordingStarted === false ? "Start Recording" : "Stop Recording"}
			</ButtonItem>
		</PanelSectionRow>
		<PanelSectionRow>
			<ButtonItem 
				label="Install needed dependencies"
				layout="below"
				disabled={dependenciesInstalled}
				onClick={() => {
					installDependencies();
				}}>
				Install needed dependencies
			</ButtonItem>
		</PanelSectionRow>
		<PanelSectionRow>
			<ButtonItem 
				label="Uninstall dependencies"
				bottomSeparator="none"
				layout="below"
				disabled={!dependenciesInstalled}
				onClick={() => {
					uninstallDependencies();
				}}>
				Uninstall dependencies
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
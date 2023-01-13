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
	useState
} from "react";

import { FaVideo } from "react-icons/fa";

const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {

	const [recordingStarted, setRecordingStarted] = useState(false);

	const recordingButtonPress = async() => {
		if (recordingStarted === false){
			setRecordingStarted(true);
			serverAPI.callPluginMethod('start_recording', {});
		} else {
			setRecordingStarted(false);
			serverAPI.callPluginMethod('end_recording', {});
		}
	}

	const installDependencies = async() => {
		await serverAPI.callPluginMethod('install_deps', {});
	}

	const uninstallDependencies = async() => {
		await serverAPI.callPluginMethod('uninstall_deps', {});
	}

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
		<PanelSectionRow>
			<ButtonItem 
				label="Install needed dependencies"
				layout="below"
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
		content: <Content serverAPI={serverApi} />,
		icon: <FaVideo />,
	};
});
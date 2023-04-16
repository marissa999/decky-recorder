import {
	definePlugin,
	ServerAPI,
	staticClasses,
} from "decky-frontend-lib";

import { DeckyRecorder } from "./DeckyRecorder";
import { DeckyRecorderLogic } from "./DeckyRecorderLogic";
import { FaVideo } from "react-icons/fa";

export default definePlugin((serverApi: ServerAPI) => {
	let logic = new DeckyRecorderLogic(serverApi);
	let input_register = window.SteamClient.Input.RegisterForControllerStateChanges(logic.handleButtonInput);
	return {
		title: <div className={staticClasses.Title}>Decky Recorder</div>,
		content: <DeckyRecorder serverAPI={serverApi} logic={logic} />,
		icon: <FaVideo />,
		onDismount() {
			input_register.unregister();
		},
		alwaysRender: true
	};
});
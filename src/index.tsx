import {
  ButtonItem,
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses,
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
      await serverAPI.callPluginMethod('start_recording', {});
    } else {
      setRecordingStarted(false);
      await serverAPI.callPluginMethod('end_recording', {});
    }
  }

  return (
    <PanelSection>
      <PanelSectionRow>
        <ButtonItem 
          label="Recordings will be saved to ~/Videos"
          bottomSeparator="none"
          layout="below"
          onClick={() => {
            recordingButtonPress();
          }}>
          {recordingStarted === false ? "Start Recording" : "Stop Recording"}
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
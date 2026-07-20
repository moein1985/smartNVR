//
//  Generated file. Do not edit.
//

// clang-format off

#include "generated_plugin_registrant.h"

#include <flutter_webrtc/flutter_web_r_t_c_plugin.h>
#include <media_kit_video/media_kit_video_plugin_c_api.h>
#include <speech_to_text_windows/speech_to_text_windows.h>
#include <volume_controller/volume_controller_plugin_c_api.h>

void RegisterPlugins(flutter::PluginRegistry* registry) {
  FlutterWebRTCPluginRegisterWithRegistrar(
      registry->GetRegistrarForPlugin("FlutterWebRTCPlugin"));
  MediaKitVideoPluginCApiRegisterWithRegistrar(
      registry->GetRegistrarForPlugin("MediaKitVideoPluginCApi"));
  SpeechToTextWindowsRegisterWithRegistrar(
      registry->GetRegistrarForPlugin("SpeechToTextWindows"));
  VolumeControllerPluginCApiRegisterWithRegistrar(
      registry->GetRegistrarForPlugin("VolumeControllerPluginCApi"));
}

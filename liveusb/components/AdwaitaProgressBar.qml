import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

ProgressBar {
    width: 100
    height: 6
    style: ProgressBarStyle {
        background: Rectangle {
            height: 6
            border {
                color: "#777777"
                width: 1
            }
            radius: 3
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#b2b2b2" }
                GradientStop { position: 1.0; color: "#d4d4d4" }
            }
        }
        progress: Rectangle {
            clip: true
            height: 4
            border {
                color: "#777777"
                width: 1
            }
            radius: 3
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#3D7DCD" }
                GradientStop { position: 0.9; color: "#54AADA" }
                GradientStop { position: 1.0; color: "#5D9DDD" }
            }
        }
    }
}


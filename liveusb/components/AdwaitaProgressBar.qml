import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

ProgressBar {
    id: root
    width: 100
    height: 6
    property color progressColor: "#54aada"
    property color backgroundColor: "#c3c3c3"
    style: ProgressBarStyle {
        background: Rectangle {
            height: 6
            border {
                color: "#777777"
                width: 1
            }
            radius: 3
            clip: true
            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.lighter(root.backgroundColor, 1.05) }
                GradientStop { position: 1.0; color: Qt.darker(root.backgroundColor, 1.05) }
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
                GradientStop { position: 0.0; color: Qt.lighter(root.progressColor, 1.05) }
                GradientStop { position: 0.9; color: root.progressColor }
                GradientStop { position: 1.0; color: Qt.darker(root.progressColor) }
            }
        }
    }
}


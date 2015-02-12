import QtQuick 2.0

Rectangle {
    id: rect
    implicitHeight: 36
    implicitWidth: 36
    radius: 3

    Rectangle {
        radius: parent.radius - 1
        anchors.margins: 0.5
        anchors.fill: parent
        gradient: control.enabled ? !control.pressed ? !control.hovered ? regularGradient: hoveredGradient : downGradient : disabledGradient
        Gradient {
            id: disabledGradient
            GradientStop { position: 0.0; color: "light gray" }
        }
        Gradient {
            id: regularGradient
            GradientStop { position: 0.0; color: "#14ffffff" }
            GradientStop { position: 1.0; color: "#14000000" }
        }
        Gradient {
            id: hoveredGradient
            GradientStop { position: 0.0; color: "#14ffffff" }
            GradientStop { position: 1.0; color: "#05ffffff" }
        }
        Gradient {
            id: downGradient
            GradientStop { position: 0.0; color: "#1e000000" }
            GradientStop { position: 1.0; color: "#14000000" }
        }
    }

    border {
        width: 1
        color: "#a1a1a1"
    }

    SystemPalette {
        id: palette
    }
}

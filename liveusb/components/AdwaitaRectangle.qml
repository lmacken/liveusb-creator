import QtQuick 2.0

Rectangle {
    id: rect
    property color tint: "transparent"
    property real tintFactor: !control.pressed ? control.hovered ? 0.0 : 0.1 : -0.2
    implicitHeight: 36
    implicitWidth: 36
    radius: 3
    color: "red"
    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.lighter(palette.button, 1.08 - (control.pressed ? 0.2 : 0)) }
        GradientStop { position: 1.0; color: Qt.lighter(palette.button, 0.92 + (!control.pressed && control.hovered ? 0.1 : 0)) }
    }
    Rectangle {
        radius: parent.radius - 1
        anchors.margins: 1
        anchors.fill: parent
        color: parent.tint
        opacity: 0.66
    }

    border {
        width: 1
        color: "#a1a1a1"
    }

    SystemPalette {
        id: palette
    }
}

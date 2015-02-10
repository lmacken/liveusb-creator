import QtQuick 2.0

Rectangle {
    id: rect
    property real tintFactor: !control.pressed ? control.hovered ? 0.0 : 0.1 : -0.2
    implicitHeight: 36
    implicitWidth: 36
    radius: 4
    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.lighter(palette.button, 1.08 - (control.pressed ? 0.2 : 0)) }
        GradientStop { position: 1.0; color: Qt.lighter(palette.button, 0.92 + (!control.pressed && control.hovered ? 0.1 : 0)) }
    }
/*
    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: 3
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#22000000" }
            GradientStop { position: 0.3; color: "#00000000" }
        }
    }
*/
    //color: control.clicked ? Qt.lighter(root.color, 1.0) : root.color
    border {
        width: 1
        color: "#b2b2b2"
    }

    SystemPalette {
        id: palette
    }
}

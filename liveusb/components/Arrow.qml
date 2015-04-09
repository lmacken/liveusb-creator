import QtQuick 2.4

Item {
    height: 10
    width: height / 2
    clip: true
    property color color: "black"
    Rectangle {
        x: -parent.height / 5 * 4
        y: -parent.height / 10
        rotation: 45
        width: parent.height
        height: parent.height
        color: parent.color
    }
}

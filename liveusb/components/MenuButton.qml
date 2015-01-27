import QtQuick 2.0
import QtQuick.Controls 1.2

Button {
    Item {
        anchors.centerIn: parent
        width: 10
        height: 10
        Column {
            spacing: 2
            Repeater {
                model: 3
                delegate: Rectangle {
                    height: 2
                    width: 10
                    radius: 2
                    color: "#444444"
                }
            }
        }
    }
}

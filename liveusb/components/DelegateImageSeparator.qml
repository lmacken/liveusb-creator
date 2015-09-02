import QtQuick 2.0
import QtQuick.Layouts 1.0

Rectangle {
    id: root

    color: "#12000000"
    width: parent.width
    height: $(32)
    Behavior on height {
        NumberAnimation {
            duration: 60
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 32
        spacing: 12
        Text {
            Layout.alignment: Qt.AlignVCenter
            font.pointSize: $(9)
            text: release.name
        }
        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            text: release.summary
            font.pointSize: $(9)
            color: "#707070"
            Behavior on opacity {
                NumberAnimation {
                    duration: 60
                }
            }
        }
    }
    Rectangle {
        height: 1
        color: "#c3c3c3"
        width: parent.width
        anchors.bottom: parent.bottom
    }
}


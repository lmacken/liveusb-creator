import QtQuick 2.0
import QtQuick.Controls 1.2

Image {
    id: root
    BusyIndicator {
        anchors.centerIn: parent
        visible: parent.status != Image.Ready
    }
}


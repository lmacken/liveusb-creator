import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

ComboBox {
    style: ComboBoxStyle {
        background: AdwaitaRectangle {
            Arrow {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 16
                rotation: 90
                scale: 1.3
            }
        }
        label: Text {
            x: 4
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            text: control.currentText
        }
    }
}

